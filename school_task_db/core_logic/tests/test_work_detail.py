from unittest import TestCase

from core_logic.entities.work import OrphanVariantRef
from core_logic.interfaces.work_repo import CreateWorkParams
from core_logic.services.work_service import WorkService
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansRequest,
    CreateWorkFromOrphansUseCase,
    DEFAULT_ORPHAN_WORK_NAME,
)
from core_logic.use_cases.generate_work_variants import (
    GenerateWorkVariantsRequest,
    GenerateWorkVariantsUseCase,
)
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
        self.generated_variants_request = None
        self.orphan_variant_refs = []
        self.created_work_params = None
        self.attached_variants_params = None

    def get_detail_variants(self, work_id):
        return self.variants

    def get_detail_analog_groups(self, work_id):
        return self.analog_groups

    def get_spec_preview(self, work_id):
        return self.spec_preview

    def sync_analog_groups_from_variants(self, work_id):
        self.synced_work_id = work_id
        return 2

    def generate_variants(self, work_id, count):
        self.generated_variants_request = (work_id, count)
        return count

    def get_orphan_variant_refs(self, variant_ids):
        requested_ids = set(variant_ids)
        return [
            variant
            for variant in self.orphan_variant_refs
            if variant.pk in requested_ids
        ]

    def attach_variants_to_work(self, params):
        self.attached_variants_params = params
        return len(params.variant_ids)

    def create_work(self, params: CreateWorkParams):
        self.created_work_params = params
        return 'created-work'


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

    def test_generate_work_variants_use_case_delegates_to_repository(self):
        repo = FakeWorkRepository()
        use_case = GenerateWorkVariantsUseCase(work_repo=repo)

        result = use_case.execute(
            GenerateWorkVariantsRequest(work_id='work-1', count=3)
        )

        self.assertEqual(result.created_count, 3)
        self.assertEqual(repo.generated_variants_request, ('work-1', 3))

    def test_create_work_from_orphans_use_case_creates_work_and_attaches_variants(self):
        repo = FakeWorkRepository()
        repo.orphan_variant_refs = [
            OrphanVariantRef(pk='variant-1', variant_type='individual', total_max_points=3),
            OrphanVariantRef(pk='variant-2', variant_type='remedial', total_max_points=5),
        ]
        use_case = CreateWorkFromOrphansUseCase(work_repo=repo)

        result = use_case.execute(
            CreateWorkFromOrphansRequest(
                variant_ids=['variant-1', 'variant-2'],
                work_name='  Повторение  ',
            )
        )

        self.assertEqual(result.status, 'created')
        self.assertEqual(result.work_id, 'created-work')
        self.assertEqual(result.work_name, 'Повторение')
        self.assertEqual(result.variant_count, 2)
        self.assertEqual(repo.created_work_params.name, 'Повторение')
        self.assertEqual(repo.created_work_params.work_type, 'remedial')
        self.assertEqual(repo.created_work_params.max_score, 5)
        self.assertEqual(repo.created_work_params.variant_counter, 2)
        self.assertEqual(repo.attached_variants_params.work_id, 'created-work')
        self.assertEqual(
            repo.attached_variants_params.variant_ids,
            ['variant-1', 'variant-2'],
        )

    def test_create_work_from_orphans_use_case_handles_empty_and_missing_selection(self):
        repo = FakeWorkRepository()
        use_case = CreateWorkFromOrphansUseCase(work_repo=repo)

        empty_result = use_case.execute(CreateWorkFromOrphansRequest(variant_ids=[]))
        missing_result = use_case.execute(
            CreateWorkFromOrphansRequest(
                variant_ids=['missing'],
                work_name='',
            )
        )

        self.assertEqual(empty_result.status, 'empty_selection')
        self.assertEqual(missing_result.status, 'not_found')

    def test_create_work_from_orphans_use_case_uses_default_name(self):
        repo = FakeWorkRepository()
        repo.orphan_variant_refs = [
            OrphanVariantRef(pk='variant-1', variant_type='regular', total_max_points=0),
        ]
        use_case = CreateWorkFromOrphansUseCase(work_repo=repo)

        result = use_case.execute(
            CreateWorkFromOrphansRequest(variant_ids=['variant-1'], work_name=' ')
        )

        self.assertEqual(result.status, 'created')
        self.assertEqual(result.work_name, DEFAULT_ORPHAN_WORK_NAME)
        self.assertEqual(repo.created_work_params.work_type, 'test')
