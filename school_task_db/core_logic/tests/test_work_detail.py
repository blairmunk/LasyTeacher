from unittest import TestCase

from core_logic.services.work_service import WorkService
from core_logic.use_cases.get_work_detail import GetWorkDetailUseCase
from core_logic.use_cases.sync_work_analog_groups import (
    SyncWorkAnalogGroupsRequest,
    SyncWorkAnalogGroupsUseCase,
)


class FakeQuerySet(list):
    def exists(self):
        return bool(self)


class FakeWorkRepository:
    def __init__(self, variants=None, analog_groups=None, spec_preview=None):
        self.variants = FakeQuerySet(variants or [])
        self.analog_groups = analog_groups or []
        self.spec_preview = spec_preview or []
        self.synced_work_id = None

    def get_detail_variants(self, work_id):
        return self.variants

    def get_detail_analog_groups(self, work_id):
        return self.analog_groups

    def get_spec_preview(self, work_id):
        return self.spec_preview

    def sync_analog_groups_from_variants(self, work_id):
        self.synced_work_id = work_id
        return 2


class WorkDetailTests(TestCase):
    def test_work_service_shows_sync_button_only_for_variants_without_groups(self):
        service = WorkService()

        self.assertTrue(
            service.should_show_sync_button(
                has_variants=True,
                has_analog_groups=False,
            )
        )
        self.assertFalse(
            service.should_show_sync_button(
                has_variants=True,
                has_analog_groups=True,
            )
        )
        self.assertFalse(
            service.should_show_sync_button(
                has_variants=False,
                has_analog_groups=False,
            )
        )

    def test_get_work_detail_use_case_builds_detail_context_data(self):
        use_case = GetWorkDetailUseCase(
            work_repo=FakeWorkRepository(
                variants=['variant-1'],
                analog_groups=[],
                spec_preview=['spec-1'],
            ),
            work_service=WorkService(),
        )

        result = use_case.execute('work-1')

        self.assertEqual(result.variants, ['variant-1'])
        self.assertEqual(result.spec_preview, ['spec-1'])
        self.assertTrue(result.show_sync_button)

    def test_sync_work_analog_groups_use_case_delegates_to_repository(self):
        repo = FakeWorkRepository()
        use_case = SyncWorkAnalogGroupsUseCase(work_repo=repo)

        result = use_case.execute(SyncWorkAnalogGroupsRequest(work_id='work-1'))

        self.assertEqual(result.created_count, 2)
        self.assertEqual(repo.synced_work_id, 'work-1')
