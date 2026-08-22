"""Django storage adapter for immutable, content-addressed image assets."""

import hashlib
import mimetypes

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from tasks.models import ImageAsset, image_asset_upload_path


class DjangoImageAssetStore:
    """Create or reuse an immutable asset identified by its SHA-256."""

    def __init__(self, storage=None):
        self.storage = storage or ImageAsset._meta.get_field('file').storage

    def get_or_create(self, uploaded_file) -> ImageAsset:
        checksum, byte_size = self._digest(uploaded_file)
        existing = ImageAsset.objects.filter(checksum=checksum).first()
        if existing is not None:
            self._restore_missing_file(existing, uploaded_file)
            return existing

        original_filename = self._filename(uploaded_file)
        asset = ImageAsset(
            checksum=checksum,
            byte_size=byte_size,
            mime_type=(
                getattr(uploaded_file, 'content_type', '')
                or mimetypes.guess_type(original_filename)[0]
                or 'application/octet-stream'
            ),
            original_filename=original_filename,
        )
        asset.file.name = self._store_file(
            asset,
            uploaded_file,
            original_filename=original_filename,
        )
        try:
            with transaction.atomic():
                asset.save(force_insert=True)
        except IntegrityError:
            existing = ImageAsset.objects.get(checksum=checksum)
            if asset.file.name != existing.file.name:
                self.storage.delete(asset.file.name)
            self._restore_missing_file(existing, uploaded_file)
            return existing
        return asset

    def _store_file(self, asset, uploaded_file, *, original_filename):
        target_name = image_asset_upload_path(asset, original_filename)
        if self.storage.exists(target_name):
            if self._stored_checksum(target_name) != asset.checksum:
                raise OSError(
                    'Файл ImageAsset не соответствует checksum в пути',
                )
            return target_name

        self._rewind(uploaded_file)
        stored_name = self.storage.save(target_name, uploaded_file)
        if stored_name == target_name:
            return stored_name

        if (
            self.storage.exists(target_name)
            and self._stored_checksum(target_name) == asset.checksum
        ):
            self.storage.delete(stored_name)
            return target_name
        self.storage.delete(stored_name)
        raise OSError('Не удалось сохранить ImageAsset по checksum-пути')

    def _stored_checksum(self, file_name):
        digest = hashlib.sha256()
        with self.storage.open(file_name, 'rb') as stored_file:
            for chunk in iter(lambda: stored_file.read(64 * 1024), b''):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _digest(uploaded_file):
        digest = hashlib.sha256()
        byte_size = 0
        for chunk in uploaded_file.chunks():
            digest.update(chunk)
            byte_size += len(chunk)
        DjangoImageAssetStore._rewind(uploaded_file)
        return digest.hexdigest(), byte_size

    @staticmethod
    def _rewind(uploaded_file):
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass

    @staticmethod
    def _filename(uploaded_file):
        return getattr(uploaded_file, 'name', '') or 'image.bin'

    def _restore_missing_file(self, asset, uploaded_file):
        if self.storage.exists(asset.file.name):
            return
        self._rewind(uploaded_file)
        restored_name = self.storage.save(asset.file.name, uploaded_file)
        if restored_name != asset.file.name:
            self.storage.delete(restored_name)
            raise OSError('Не удалось восстановить файл ImageAsset по прежнему пути')


class DjangoImageAssetFileResolver:
    """Resolve immutable snapshot references without exposing ORM objects."""

    @staticmethod
    def file_name(asset_id: str) -> str:
        if not asset_id:
            return ''
        try:
            return (
                ImageAsset.objects.filter(pk=asset_id)
                .values_list('file', flat=True)
                .first()
                or ''
            )
        except (TypeError, ValueError, ValidationError):
            return ''
