from unittest import TestCase

from core_logic.entities.document import PrintSettingsSpec
from core_logic.entities.work import (
    OrphanVariantRef,
    RemedialSheetData,
    VariantDeleteInfo,
    VariantDetailTask,
    VariantDetailTaskRow,
    VariantDetailVariant,
    WorkDetailAnalogGroup,
    WorkDetailContentBlock,
    WorkDetailSpecGroup,
    WorkDetailWork,
    WorkListFilters,
)
from core_logic.entities.work_variant_composition import (
    WorkVariantCompositionInput,
    WorkVariantCompositionSaveResult,
)
from core_logic.interfaces.orphan_variant_repo import (
    CreatedWorkFromOrphanVariantsRef,
)
from core_logic.services.work_service import WorkService
from core_logic.use_cases.bulk_delete_variants import (
    BulkDeleteVariantsRequest,
    BulkDeleteVariantsUseCase,
)
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansRequest,
    CreateWorkFromOrphansUseCase,
    DEFAULT_ORPHAN_WORK_NAME,
)
from core_logic.use_cases.delete_variant import (
    DeleteVariantRequest,
    DeleteVariantUseCase,
)
from core_logic.use_cases.compose_work_variants import (
    ComposeWorkVariantsRequest,
    ComposeWorkVariantsUseCase,
)
from core_logic.use_cases.get_variant_delete_info import GetVariantDeleteInfoUseCase
from core_logic.use_cases.get_variant_detail import GetVariantDetailUseCase
from core_logic.use_cases.get_variant_list import GetVariantListUseCase
from core_logic.use_cases.get_orphan_variant_list import GetOrphanVariantListUseCase
from core_logic.use_cases.get_remedial_sheet_data import (
    GetRemedialSheetDataUseCase,
)
from core_logic.use_cases.get_work_detail import GetWorkDetailUseCase
from core_logic.use_cases.get_work_form_data import GetWorkFormDataUseCase
from core_logic.use_cases.get_work_list import GetWorkListUseCase
from core_logic.use_cases.sync_work_analog_groups import (
    SyncWorkAnalogGroupsRequest,
    SyncWorkAnalogGroupsUseCase,
)


class FakeQuerySet(list):
    def exists(self):
        return bool(self)


class FakeVariant:
    def __init__(self, work=None):
        self.work = work


class FakeWork:
    pk = 'work-1'


class FakeWorkRepository:
    def __init__(
        self,
        variants=None,
        analog_groups=None,
        spec_preview=None,
        content_blocks=None,
    ):
        self.variants = FakeQuerySet(variants or [])
        self.list_variants = FakeQuerySet()
        self.works = FakeQuerySet()
        self.work_form_analog_group_options = []
        self.analog_groups = analog_groups or []
        self.content_blocks = content_blocks or []
        self.spec_preview = spec_preview or []
        self.variant_detail_tasks = []
        self.variant_detail = VariantDetailVariant(
            pk='variant-1',
            number=1,
            display_name='Контрольная',
            short_uuid='abcd1234',
            medium_uuid='abcd1234-efgh',
            variant_type='regular',
            variant_type_display='Обычный',
            display_duration=45,
            display_max_score=7,
            created_at=None,
        )
        self.variant_total_max_points = 0
        self.orphan_variants = FakeQuerySet()
        self.orphan_variant_count = 0
        self.synced_work_id = None
        self.generated_variants_request = None
        self.variant_composition_input_requests = []
        self.variant_composition_save_requests = []
        self.variant_composition_save_statuses = []
        self.orphan_variant_refs = []
        self.created_from_orphans_params = None
        self.create_from_orphans_result = CreatedWorkFromOrphanVariantsRef(
            work_id='created-work',
            variant_count=0,
        )
        self.variant_delete_info = VariantDeleteInfo(task_count=0)
        self.detached_variant_id = None
        self.deleted_variant_id = None
        self.bulk_deleted_request = None
        self.remaining_variant_count = 0
        self.remedial_sheet_data = RemedialSheetData(
            variant='remedial-variant',
            student='student',
            source_work='source-work',
            mark='mark',
            original_tasks=['original-task'],
            new_tasks=['new-task'],
        )
        self.remedial_sheet_variant_id = None
        self.work_name = 'Контрольная'
        self.work_name_request = None
        self.work_exists_for_spec_sync = True
        self.work_exists_for_composition = True
        self.work_list_filters = None
        self.variant_type = 'remedial'
        self.variant_type_request = None
        self.work_variant_ids = []
        self.work_variant_ids_request = None
        self.work_detail = WorkDetailWork(
            pk='work-1',
            name='Контрольная',
            work_type='test',
            work_type_display='Контрольная работа',
            duration=45,
            max_score=0,
            effective_max_score=0,
            variant_count=0,
            created_at=None,
            updated_at=None,
        )

    def get_work_detail(self, work_id):
        return self.work_detail if work_id == self.work_detail.pk else None

    def get_detail_variants(self, work_id):
        return self.variants

    def get_list_works(self, filters=None):
        self.work_list_filters = filters
        return self.works

    def get_list_variants(self):
        return self.list_variants

    def get_work_form_analog_group_options(self):
        return self.work_form_analog_group_options

    def get_work_name(self, work_id):
        self.work_name_request = work_id
        return self.work_name

    def get_detail_analog_groups(self, work_id):
        return self.analog_groups

    def get_detail_content_blocks(self, work_id):
        return self.content_blocks

    def get_spec_preview(self, work_id):
        return self.spec_preview

    def get_variant_detail_tasks(self, variant_id):
        return self.variant_detail_tasks

    def get_variant_detail(self, variant_id):
        return self.variant_detail if variant_id == self.variant_detail.pk else None

    def get_variant_total_max_points(self, variant_id):
        return self.variant_total_max_points

    def get_variant_type(self, variant_id):
        self.variant_type_request = variant_id
        return self.variant_type

    def get_work_variant_ids(self, work_id):
        self.work_variant_ids_request = work_id
        return self.work_variant_ids

    def get_remedial_sheet_data(self, variant_id):
        self.remedial_sheet_variant_id = variant_id
        return self.remedial_sheet_data

    def get_orphan_variants(self):
        return self.orphan_variants

    def count_orphan_variants(self):
        return self.orphan_variant_count

    def sync_analog_groups_from_variants(self, work_id):
        self.synced_work_id = work_id
        return 2 if self.work_exists_for_spec_sync else None

    def get_variant_composition_input(self, work_id):
        self.variant_composition_input_requests.append(work_id)
        if not self.work_exists_for_composition:
            return None
        return WorkVariantCompositionInput(
            work_name='Контрольная',
            duration=45,
            max_score=0,
            effective_max_score=0,
            variant_counter=len(self.variant_composition_input_requests) - 1,
        )

    def save_variant_composition_plan(
        self,
        work_id,
        expected_variant_counter,
        plan,
    ):
        self.generated_variants_request = (work_id, len(plan.variants))
        self.variant_composition_save_requests.append(
            (work_id, expected_variant_counter, plan),
        )
        status = (
            self.variant_composition_save_statuses.pop(0)
            if self.variant_composition_save_statuses
            else 'saved'
        )
        return WorkVariantCompositionSaveResult(status=status)

    def get_orphan_variant_refs(self, variant_ids):
        requested_ids = set(variant_ids)
        return [
            variant
            for variant in self.orphan_variant_refs
            if variant.pk in requested_ids
        ]

    def create_work_from_orphan_variants(self, params):
        self.created_from_orphans_params = params
        if self.create_from_orphans_result is None:
            return None
        return CreatedWorkFromOrphanVariantsRef(
            work_id=self.create_from_orphans_result.work_id,
            variant_count=len(params.variant_ids),
        )

    def get_variant_delete_info(self, variant_id):
        return self.variant_delete_info

    def detach_variant_from_work(self, variant_id):
        self.detached_variant_id = variant_id
        return 'ABCD'

    def delete_variant(self, variant_id):
        self.deleted_variant_id = variant_id
        return 'work-1'

    def bulk_delete_work_variants(self, work_id, variant_ids):
        self.bulk_deleted_request = (work_id, variant_ids)
        return len(variant_ids)

    def count_work_variants(self, work_id):
        return self.remaining_variant_count


class FakePrintSettingsRepository:
    def __init__(self):
        self.requested_document_types = []
        self.print_settings_by_type = {
            'work': [
                PrintSettingsSpec(
                    name='Шаблон работы',
                    document_type='work',
                    print_settings_id='template-work',
                ),
            ],
            'remedial_sheet': [
                PrintSettingsSpec(
                    name='Шаблон РнО',
                    document_type='remedial_sheet',
                    print_settings_id='template-remedial',
                ),
            ],
        }

    def list_print_settings_specs(self, document_type=''):
        self.requested_document_types.append(document_type)
        return self.print_settings_by_type.get(document_type, [])

    def get_default_print_settings_spec(self, document_type):
        return None

    def get_print_settings_spec(self, print_settings_id, document_type=''):
        return None


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
        print_settings_repo = FakePrintSettingsRepository()
        use_case = GetWorkDetailUseCase(
            work_read_repo=FakeWorkRepository(
                variants=['variant-1'],
                analog_groups=[],
                spec_preview=['spec-1'],
            ),
            work_service=WorkService(),
            print_settings_repo=print_settings_repo,
        )
        self.assertIs(use_case.print_settings_repo, print_settings_repo)

        result = use_case.execute('work-1')

        self.assertEqual(result.work.name, 'Контрольная')
        self.assertEqual(result.variants, ['variant-1'])
        self.assertEqual(result.spec_preview, ['spec-1'])
        self.assertEqual(
            result.work_print_settings[0].print_settings_id,
            'template-work',
        )
        self.assertEqual(
            result.remedial_sheet_print_settings[0].print_settings_id,
            'template-remedial',
        )
        self.assertEqual(
            print_settings_repo.requested_document_types,
            ['work', 'remedial_sheet'],
        )
        self.assertTrue(result.show_sync_button)

    def test_get_work_detail_builds_task_selection_content_plan(self):
        spec_row = WorkDetailSpecGroup(
            order=3,
            analog_group=WorkDetailAnalogGroup(
                pk='group-1',
                name='Законы Ньютона',
            ),
            count=2,
            weight=4,
        )
        use_case = GetWorkDetailUseCase(
            work_read_repo=FakeWorkRepository(
                analog_groups=[spec_row],
            ),
            work_service=WorkService(),
        )

        result = use_case.execute('work-1')

        selection = result.content_plan.task_selections[0]
        self.assertEqual(selection.analog_group_id, 'group-1')
        self.assertEqual(selection.count, 2)
        self.assertEqual(selection.order, 3)
        self.assertEqual(selection.weight, 4)

    def test_get_work_detail_merges_persistent_content_in_pedagogical_order(self):
        content_blocks = [
            WorkDetailContentBlock(
                pk='content-2',
                content_type='text',
                order=20,
                title='Инструкция',
                body='Решите самостоятельно.',
            ),
            WorkDetailContentBlock(
                pk='content-1',
                content_type='theory',
                order=5,
                title='Теория',
                topic_ids=('topic-1', 'topic-2'),
                include_subtopics=True,
            ),
        ]
        use_case = GetWorkDetailUseCase(
            work_read_repo=FakeWorkRepository(
                content_blocks=content_blocks,
            ),
            work_service=WorkService(),
        )

        result = use_case.execute('work-1')

        self.assertEqual(
            [block.content_type for block in result.content_plan.blocks],
            ['theory', 'text'],
        )
        theory, text = result.content_plan.blocks
        self.assertEqual(theory.topic_ids, ('topic-1', 'topic-2'))
        self.assertTrue(theory.include_subtopics)
        self.assertEqual(text.body, 'Решите самостоятельно.')

    def test_get_work_detail_use_case_returns_empty_data_for_missing_work(self):
        repo = FakeWorkRepository()
        use_case = GetWorkDetailUseCase(
            work_read_repo=repo,
            work_service=WorkService(),
        )

        result = use_case.execute('missing-work')

        self.assertIsNone(result.work)
        self.assertEqual(result.variants, [])

    def test_get_work_list_use_case_builds_list_context_data(self):
        repo = FakeWorkRepository()
        repo.works = FakeQuerySet(['work-1'])
        use_case = GetWorkListUseCase(work_read_repo=repo)

        result = use_case.execute()

        self.assertEqual(result.works, ['work-1'])
        self.assertEqual(result.filters, WorkListFilters())

    def test_get_work_list_use_case_passes_filters_to_repository(self):
        repo = FakeWorkRepository()
        filters = WorkListFilters(
            q='контрольная',
            work_type='test',
            variant_status='with_variants',
            hide_remedial=True,
        )
        use_case = GetWorkListUseCase(work_read_repo=repo)

        result = use_case.execute(filters)

        self.assertEqual(repo.work_list_filters, filters)
        self.assertEqual(result.filters, filters)

    def test_get_variant_list_use_case_builds_list_context_data(self):
        repo = FakeWorkRepository()
        repo.list_variants = FakeQuerySet(['variant-1'])
        use_case = GetVariantListUseCase(variant_repo=repo)

        result = use_case.execute()

        self.assertEqual(result.variants, ['variant-1'])

    def test_get_work_form_data_use_case_builds_form_context_data(self):
        repo = FakeWorkRepository()
        repo.work_form_analog_group_options = ['group-1']
        use_case = GetWorkFormDataUseCase(work_read_repo=repo)

        result = use_case.execute()

        self.assertEqual(result.analog_group_options, ['group-1'])

    def test_get_variant_detail_use_case_builds_detail_context_data(self):
        repo = FakeWorkRepository()
        repo.variant_detail_tasks = [
            VariantDetailTaskRow(
                task=VariantDetailTask(
                    pk='task-1',
                    id='task-1',
                    topic='Кинематика',
                    text='Задача',
                    answer='Ответ',
                    task_type_display='Расчётная задача',
                    difficulty=2,
                    short_uuid='task1234',
                ),
                order=1,
                max_points=2,
            )
        ]
        repo.variant_total_max_points = 7
        use_case = GetVariantDetailUseCase(variant_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(result.variant, repo.variant_detail)
        self.assertEqual(result.variant_tasks, repo.variant_detail_tasks)
        self.assertEqual(result.total_max_points, 7)

    def test_get_variant_detail_use_case_returns_empty_data_for_missing_variant(self):
        repo = FakeWorkRepository()
        use_case = GetVariantDetailUseCase(variant_repo=repo)

        result = use_case.execute('missing-variant')

        self.assertIsNone(result.variant)
        self.assertEqual(result.variant_tasks, [])

    def test_get_remedial_sheet_data_use_case_returns_repository_data(self):
        repo = FakeWorkRepository()
        use_case = GetRemedialSheetDataUseCase(work_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(repo.remedial_sheet_variant_id, 'variant-1')
        self.assertEqual(result, repo.remedial_sheet_data)

    def test_get_remedial_sheet_data_use_case_handles_missing_variant(self):
        repo = FakeWorkRepository()
        repo.remedial_sheet_data = None
        use_case = GetRemedialSheetDataUseCase(work_repo=repo)

        result = use_case.execute('missing')

        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(result.variant)
        self.assertEqual(repo.remedial_sheet_variant_id, 'missing')

    def test_get_remedial_sheet_data_use_case_handles_missing_source(self):
        repo = FakeWorkRepository()
        repo.remedial_sheet_data = RemedialSheetData(
            variant=FakeVariant(work=FakeWork()),
            student='student',
            source_work=None,
            mark=None,
        )
        use_case = GetRemedialSheetDataUseCase(work_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(result.status, 'missing_source')
        self.assertEqual(result.redirect_work_id, 'work-1')

    def test_get_remedial_sheet_data_use_case_handles_missing_student(self):
        repo = FakeWorkRepository()
        repo.remedial_sheet_data = RemedialSheetData(
            variant=FakeVariant(),
            student=None,
            source_work='source-work',
            mark=None,
        )
        use_case = GetRemedialSheetDataUseCase(work_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(result.status, 'missing_student')
        self.assertIn('ученика', result.message)

    def test_get_orphan_variant_list_use_case_builds_list_context_data(self):
        repo = FakeWorkRepository()
        repo.orphan_variants = FakeQuerySet(['variant-1'])
        repo.orphan_variant_count = 1
        use_case = GetOrphanVariantListUseCase(orphan_variant_repo=repo)

        result = use_case.execute()

        self.assertEqual(result.variants, ['variant-1'])
        self.assertEqual(result.total_orphans, 1)

    def test_sync_work_analog_groups_use_case_delegates_to_repository(self):
        repo = FakeWorkRepository()
        use_case = SyncWorkAnalogGroupsUseCase(work_repo=repo)

        result = use_case.execute(SyncWorkAnalogGroupsRequest(work_id='work-1'))

        self.assertEqual(result.status, 'synced')
        self.assertEqual(result.created_count, 2)
        self.assertEqual(repo.synced_work_id, 'work-1')

    def test_sync_work_analog_groups_use_case_handles_missing_work(self):
        repo = FakeWorkRepository()
        repo.work_exists_for_spec_sync = False
        use_case = SyncWorkAnalogGroupsUseCase(work_repo=repo)

        result = use_case.execute(SyncWorkAnalogGroupsRequest(work_id='missing'))

        self.assertEqual(result.status, 'not_found')
        self.assertEqual(result.created_count, 0)
        self.assertEqual(repo.synced_work_id, 'missing')

    def test_compose_work_variants_use_case_delegates_to_repository(self):
        repo = FakeWorkRepository()
        use_case = ComposeWorkVariantsUseCase(work_repo=repo)

        result = use_case.execute(
            ComposeWorkVariantsRequest(work_id='work-1', count=3)
        )

        self.assertEqual(result.status, 'generated')
        self.assertEqual(result.created_count, 3)
        self.assertEqual(repo.variant_composition_input_requests, ['work-1'])
        self.assertEqual(repo.generated_variants_request, ('work-1', 3))

    def test_compose_work_variants_use_case_handles_missing_work(self):
        repo = FakeWorkRepository()
        repo.work_exists_for_composition = False
        use_case = ComposeWorkVariantsUseCase(work_repo=repo)

        result = use_case.execute(
            ComposeWorkVariantsRequest(work_id='missing', count=3)
        )

        self.assertEqual(result.status, 'not_found')
        self.assertEqual(result.created_count, 0)
        self.assertEqual(repo.variant_composition_input_requests, ['missing'])
        self.assertIsNone(repo.generated_variants_request)

    def test_compose_work_variants_use_case_retries_counter_conflict(self):
        repo = FakeWorkRepository()
        repo.variant_composition_save_statuses = ['conflict', 'saved']
        use_case = ComposeWorkVariantsUseCase(work_repo=repo)

        result = use_case.execute(
            ComposeWorkVariantsRequest(work_id='work-1', count=2)
        )

        self.assertEqual(result.status, 'generated')
        self.assertEqual(result.created_count, 2)
        self.assertEqual(
            repo.variant_composition_input_requests,
            ['work-1', 'work-1'],
        )
        self.assertEqual(
            [
                request[1]
                for request in repo.variant_composition_save_requests
            ],
            [0, 1],
        )

    def test_compose_work_variants_use_case_reports_repeated_conflict(self):
        repo = FakeWorkRepository()
        repo.variant_composition_save_statuses = ['conflict'] * 3
        use_case = ComposeWorkVariantsUseCase(work_repo=repo)

        result = use_case.execute(
            ComposeWorkVariantsRequest(work_id='work-1', count=2)
        )

        self.assertEqual(result.status, 'conflict')
        self.assertEqual(result.created_count, 0)
        self.assertEqual(len(repo.variant_composition_save_requests), 3)

    def test_create_work_from_orphans_use_case_creates_work_and_attaches_variants(self):
        repo = FakeWorkRepository()
        repo.orphan_variant_refs = [
            OrphanVariantRef(pk='variant-1', variant_type='individual', total_max_points=3),
            OrphanVariantRef(pk='variant-2', variant_type='remedial', total_max_points=5),
        ]
        use_case = CreateWorkFromOrphansUseCase(orphan_variant_repo=repo)

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
        self.assertEqual(repo.created_from_orphans_params.name, 'Повторение')
        self.assertEqual(repo.created_from_orphans_params.work_type, 'remedial')
        self.assertEqual(repo.created_from_orphans_params.max_score, 5)
        self.assertEqual(
            repo.created_from_orphans_params.variant_ids,
            ['variant-1', 'variant-2'],
        )

    def test_create_work_from_orphans_use_case_handles_empty_and_missing_selection(self):
        repo = FakeWorkRepository()
        use_case = CreateWorkFromOrphansUseCase(orphan_variant_repo=repo)

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
        use_case = CreateWorkFromOrphansUseCase(orphan_variant_repo=repo)

        result = use_case.execute(
            CreateWorkFromOrphansRequest(variant_ids=['variant-1'], work_name=' ')
        )

        self.assertEqual(result.status, 'created')
        self.assertEqual(result.work_name, DEFAULT_ORPHAN_WORK_NAME)
        self.assertEqual(repo.created_from_orphans_params.work_type, 'test')

    def test_create_work_from_orphans_handles_concurrent_variant_attachment(self):
        repo = FakeWorkRepository()
        repo.orphan_variant_refs = [
            OrphanVariantRef(
                pk='variant-1',
                variant_type='remedial',
                total_max_points=3,
            ),
        ]
        repo.create_from_orphans_result = None

        result = CreateWorkFromOrphansUseCase(orphan_variant_repo=repo).execute(
            CreateWorkFromOrphansRequest(variant_ids=['variant-1'])
        )

        self.assertEqual(result.status, 'not_found')

    def test_get_variant_delete_info_use_case_delegates_to_repository(self):
        repo = FakeWorkRepository()
        repo.variant_delete_info = VariantDeleteInfo(
            task_count=3,
            participation_count=1,
        )
        use_case = GetVariantDeleteInfoUseCase(variant_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(result.task_count, 3)
        self.assertTrue(result.has_participations)

    def test_get_variant_delete_info_use_case_returns_none_for_missing_variant(self):
        repo = FakeWorkRepository()
        repo.variant_delete_info = None
        use_case = GetVariantDeleteInfoUseCase(variant_repo=repo)

        result = use_case.execute('missing-variant')

        self.assertIsNone(result)

    def test_delete_variant_use_case_returns_not_found_for_missing_variant(self):
        repo = FakeWorkRepository()
        repo.variant_delete_info = None
        use_case = DeleteVariantUseCase(variant_repo=repo)

        result = use_case.execute(
            DeleteVariantRequest(variant_id='missing-variant', action='delete')
        )

        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(repo.deleted_variant_id)

    def test_delete_variant_use_case_blocks_delete_when_variant_has_participations(self):
        repo = FakeWorkRepository()
        repo.variant_delete_info = VariantDeleteInfo(
            task_count=2,
            participation_count=1,
        )
        use_case = DeleteVariantUseCase(variant_repo=repo)

        result = use_case.execute(
            DeleteVariantRequest(variant_id='variant-1', action='delete')
        )

        self.assertEqual(result.status, 'blocked_has_participations')
        self.assertEqual(result.participation_count, 1)
        self.assertIsNone(repo.deleted_variant_id)

    def test_delete_variant_use_case_detaches_variant(self):
        repo = FakeWorkRepository()
        use_case = DeleteVariantUseCase(variant_repo=repo)

        result = use_case.execute(
            DeleteVariantRequest(variant_id='variant-1', action='detach')
        )

        self.assertEqual(result.status, 'detached')
        self.assertEqual(result.variant_short_id, 'ABCD')
        self.assertEqual(repo.detached_variant_id, 'variant-1')

    def test_delete_variant_use_case_deletes_variant_without_participations(self):
        repo = FakeWorkRepository()
        use_case = DeleteVariantUseCase(variant_repo=repo)

        result = use_case.execute(
            DeleteVariantRequest(variant_id='variant-1', action='delete')
        )

        self.assertEqual(result.status, 'deleted')
        self.assertEqual(result.redirect_work_id, 'work-1')
        self.assertEqual(repo.deleted_variant_id, 'variant-1')

    def test_bulk_delete_variants_use_case_deletes_selected_variants(self):
        repo = FakeWorkRepository()
        repo.remaining_variant_count = 4
        use_case = BulkDeleteVariantsUseCase(variant_repo=repo)

        result = use_case.execute(
            BulkDeleteVariantsRequest(
                work_id='work-1',
                variant_ids=['variant-1', 'variant-2'],
            )
        )

        self.assertEqual(result.status, 'deleted')
        self.assertEqual(result.deleted_count, 2)
        self.assertEqual(result.remaining_count, 4)
        self.assertEqual(
            repo.bulk_deleted_request,
            ('work-1', ['variant-1', 'variant-2']),
        )

    def test_bulk_delete_variants_use_case_handles_empty_selection(self):
        repo = FakeWorkRepository()
        use_case = BulkDeleteVariantsUseCase(variant_repo=repo)

        result = use_case.execute(
            BulkDeleteVariantsRequest(work_id='work-1', variant_ids=[])
        )

        self.assertEqual(result.status, 'empty_selection')
        self.assertIsNone(repo.bulk_deleted_request)
