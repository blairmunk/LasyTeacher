"""Resolve immutable task-snapshot image references to storage file names."""

from infrastructure.services.django_image_asset_store import (
    DjangoImageAssetFileResolver,
)


class TaskSnapshotImageFileResolver:
    """Prefer immutable asset UUIDs while retaining legacy snapshot reads."""

    def __init__(self, asset_file_resolver=None):
        self.asset_file_resolver = (
            asset_file_resolver or DjangoImageAssetFileResolver()
        )

    def file_name(
        self,
        *,
        asset_id: str = '',
        legacy_file_name: str = '',
        cache=None,
    ) -> str:
        if not asset_id:
            return legacy_file_name

        if cache is not None and asset_id in cache:
            return cache[asset_id]

        file_name = self.asset_file_resolver.file_name(asset_id)
        if cache is not None:
            cache[asset_id] = file_name
        return file_name
