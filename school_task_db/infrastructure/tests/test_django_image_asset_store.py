import hashlib
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from infrastructure.services.django_image_asset_store import (
    DjangoImageAssetStore,
)
from tasks.models import ImageAsset


class DjangoImageAssetStoreTests(TestCase):
    def test_reuses_asset_for_identical_binary_content(self):
        with TemporaryDirectory() as media_root, self.settings(
            MEDIA_ROOT=media_root,
        ):
            store = DjangoImageAssetStore()

            first = store.get_or_create(self._upload('first.png', b'image'))
            second = store.get_or_create(self._upload('second.jpg', b'image'))

            self.assertEqual(first.pk, second.pk)
            self.assertEqual(ImageAsset.objects.count(), 1)
            self.assertEqual(
                first.checksum,
                hashlib.sha256(b'image').hexdigest(),
            )
            self.assertEqual(first.byte_size, 5)
            self.assertTrue(first.file.storage.exists(first.file.name))

    def test_different_content_creates_new_immutable_asset(self):
        with TemporaryDirectory() as media_root, self.settings(
            MEDIA_ROOT=media_root,
        ):
            store = DjangoImageAssetStore()
            first = store.get_or_create(self._upload('image.png', b'first'))
            second = store.get_or_create(self._upload('image.png', b'second'))

            self.assertNotEqual(first.pk, second.pk)
            self.assertEqual(ImageAsset.objects.count(), 2)
            with self.assertRaises(ValidationError):
                first.save()
            with self.assertRaises(ValidationError):
                first.delete()

    def test_same_content_restores_missing_physical_file(self):
        with TemporaryDirectory() as media_root, self.settings(
            MEDIA_ROOT=media_root,
        ):
            store = DjangoImageAssetStore()
            original = store.get_or_create(
                self._upload('image.png', b'restorable'),
            )
            original.file.storage.delete(original.file.name)
            self.assertFalse(original.file.storage.exists(original.file.name))

            restored = store.get_or_create(
                self._upload('replacement.png', b'restorable'),
            )

            self.assertEqual(restored.pk, original.pk)
            self.assertTrue(restored.file.storage.exists(restored.file.name))
            with restored.file.open('rb') as restored_file:
                self.assertEqual(restored_file.read(), b'restorable')

    def test_reuses_orphaned_checksum_file_without_random_suffix(self):
        with TemporaryDirectory() as media_root:
            storage = FileSystemStorage(location=media_root)
            checksum = hashlib.sha256(b'orphaned').hexdigest()
            target_name = f'image_assets/{checksum[:2]}/{checksum}.png'
            storage.save(target_name, self._upload('old.png', b'orphaned'))

            asset = DjangoImageAssetStore(storage=storage).get_or_create(
                self._upload('new.png', b'orphaned'),
            )

            self.assertEqual(asset.file.name, target_name)
            self.assertEqual(
                storage.listdir(f'image_assets/{checksum[:2]}')[1],
                [f'{checksum}.png'],
            )

    @staticmethod
    def _upload(name, content):
        return SimpleUploadedFile(
            name,
            content,
            content_type='image/png',
        )
