"""Resolve task-image snapshots for standalone document renderers."""

import mimetypes
from pathlib import Path

from django.core.files.storage import default_storage

from core_logic.services.task_image_transfer_codec import (
    TaskImageTransferCodec,
)
from core_logic.value_objects.task_image_position import task_image_layout
from infrastructure.services.task_snapshot_image_files import (
    TaskSnapshotImageFileResolver,
)


class TaskDocumentImagePayloadFormatter:
    """Add target-specific sources to storage-neutral image metadata."""

    def __init__(
        self,
        storage=None,
        transfer_codec=None,
        asset_file_resolver=None,
        snapshot_image_file_resolver=None,
    ):
        self.storage = storage or default_storage
        self.transfer_codec = transfer_codec or TaskImageTransferCodec()
        self.snapshot_image_file_resolver = (
            snapshot_image_file_resolver
            or TaskSnapshotImageFileResolver(asset_file_resolver)
        )

    def format_task_payload(self, payload, request=None):
        formatted = dict(payload)
        images = tuple(
            image
            for image in (
                self._format_image(item, request=request)
                for item in payload.get('images', ())
            )
            if image is not None
        )
        formatted['images'] = images
        formatted['right_images'] = tuple(
            image for image in images if image['placement'] == 'right'
        )
        formatted['bottom_images'] = tuple(
            image for image in images if image['placement'] == 'bottom'
        )
        return formatted

    def _format_image(self, image, *, request=None):
        image = dict(image)
        file_name = self._file_name(image, request=request)
        if not file_name or not self._exists(file_name):
            return None

        renderer_type = self._renderer_type(request)
        render_source = self._cached_render_source(
            file_name,
            renderer_type=renderer_type,
            request=request,
        )
        if not render_source:
            return None

        layout = task_image_layout(image.get('position', ''))
        return {
            **image,
            'file_name': file_name,
            'render_source': render_source,
            'placement': layout.placement,
            'width_percent': layout.width_percent,
            'width_fraction': f'{layout.width_percent / 100:g}',
        }

    def _file_name(self, image, *, request=None):
        build_context = getattr(request, 'build_context', None)
        cache = None
        if build_context is not None:
            cache = build_context.setdefault('image_asset_file_names', {})
        return self.snapshot_image_file_resolver.file_name(
            asset_id=image.get('asset_id', ''),
            legacy_file_name=image.get('file_name', ''),
            cache=cache,
        )

    def _cached_render_source(self, file_name, *, renderer_type, request):
        build_context = getattr(request, 'build_context', None)
        cache = None
        cache_key = (renderer_type, file_name)
        if build_context is not None:
            cache = build_context.setdefault('task_image_render_sources', {})
            if cache_key in cache:
                return cache[cache_key]

        source = self._render_source(file_name, renderer_type)
        if cache is not None:
            cache[cache_key] = source
        return source

    def _render_source(self, file_name, renderer_type):
        try:
            if renderer_type == 'latex':
                absolute_path = Path(self.storage.path(file_name)).resolve()
                return r'{\detokenize{' + str(absolute_path) + '}}'

            mime_type = (
                mimetypes.guess_type(file_name)[0]
                or 'application/octet-stream'
            )
            with self.storage.open(file_name, 'rb') as image_file:
                encoded = self.transfer_codec.encode(image_file.read())
            return f'data:{mime_type};base64,{encoded}'
        except (OSError, TypeError, ValueError, NotImplementedError):
            return ''

    def _exists(self, file_name):
        try:
            return self.storage.exists(file_name)
        except Exception:
            return False

    @staticmethod
    def _renderer_type(request):
        render_target = getattr(request, 'render_target', None)
        return getattr(render_target, 'renderer_type', '') or 'html'
