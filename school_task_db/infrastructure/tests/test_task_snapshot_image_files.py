from django.test import SimpleTestCase

from infrastructure.services.task_snapshot_image_files import (
    TaskSnapshotImageFileResolver,
)


class TaskSnapshotImageFileResolverTests(SimpleTestCase):
    def test_resolves_asset_uuid_and_caches_file_name(self):
        asset_resolver = FakeAssetFileResolver('image_assets/current.png')
        resolver = TaskSnapshotImageFileResolver(asset_resolver)
        cache = {}

        first = resolver.file_name(
            asset_id='asset-1',
            legacy_file_name='task_images/stale.png',
            cache=cache,
        )
        second = resolver.file_name(
            asset_id='asset-1',
            legacy_file_name='task_images/other.png',
            cache=cache,
        )

        self.assertEqual(first, 'image_assets/current.png')
        self.assertEqual(second, first)
        self.assertEqual(asset_resolver.asset_ids, ['asset-1'])

    def test_does_not_fall_back_when_asset_uuid_cannot_be_resolved(self):
        resolver = TaskSnapshotImageFileResolver(
            FakeAssetFileResolver(''),
        )

        file_name = resolver.file_name(
            asset_id='missing-asset',
            legacy_file_name='task_images/stale.png',
        )

        self.assertEqual(file_name, '')

    def test_reads_physical_path_from_legacy_snapshot_without_asset_uuid(self):
        asset_resolver = FakeAssetFileResolver('unused.png')
        resolver = TaskSnapshotImageFileResolver(asset_resolver)

        file_name = resolver.file_name(
            legacy_file_name='task_images/legacy.png',
        )

        self.assertEqual(file_name, 'task_images/legacy.png')
        self.assertEqual(asset_resolver.asset_ids, [])


class FakeAssetFileResolver:
    def __init__(self, resolved_file_name):
        self.resolved_file_name = resolved_file_name
        self.asset_ids = []

    def file_name(self, asset_id):
        self.asset_ids.append(asset_id)
        return self.resolved_file_name
