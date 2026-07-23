from unittest import TestCase

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.entities.work import (
    OrphanVariantRef,
    RemedialSheetData,
    VariantDeleteInfo,
    VariantDetailTask,
    VariantDetailTaskRow,
    VariantDetailVariant,
    VariantGenerationInfo,
    WorkDetailWork,
    WorkListFilters,
)
from core_logic.interfaces.work_repo import CreateWorkParams
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
from core_logic.use_cases.get_variant_generation_placeholder import (
    GetVariantGenerationPlaceholderUseCase,
)
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
from core_logic.value_objects.document_render_options import (
    WORK_DOCUMENT_STYLE_WORKSHEET,
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
    def __init__(self, variants=None, analog_groups=None, spec_preview=None):
        self.variants = FakeQuerySet(variants or [])
        self.list_variants = FakeQuerySet()
        self.works = FakeQuerySet()
        self.work_form_analog_group_options = []
        self.analog_groups = analog_groups or []
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
        self.orphan_variant_refs = []
        self.created_work_params = None
        self.attached_variants_params = None
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
        self.variant_generation_info = VariantGenerationInfo(
            number=3,
            work_name='Контрольная',
        )
        self.variant_generation_id = None
        self.work_name = 'Контрольная'
        self.work_name_request = None
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

    def get_variant_generation_info(self, variant_id):
        self.variant_generation_id = variant_id
        return self.variant_generation_info

    def get_remedial_sheet_data(self, variant_id):
        self.remedial_sheet_variant_id = variant_id
        return self.remedial_sheet_data

    def get_orphan_variants(self):
        return self.orphan_variants

    def count_orphan_variants(self):
        return self.orphan_variant_count

    def sync_analog_groups_from_variants(self, work_id):
        self.synced_work_id = work_id
        return 2

    def compose_variants(self, work_id, count):
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


class FakeDocumentTemplateRepository:
    def __init__(self):
        self.requested_template_types = []
        self.templates_by_type = {
            'work': [
                DocumentTemplateSpec(
                    name='Шаблон работы',
                    template_type='work',
                    template_id='template-work',
                ),
            ],
            'remedial_sheet': [
                DocumentTemplateSpec(
                    name='Шаблон РнО',
                    template_type='remedial_sheet',
                    template_id='template-remedial',
                ),
            ],
        }

    def list_template_specs(self, template_type=''):
        self.requested_template_types.append(template_type)
        return self.templates_by_type.get(template_type, [])

    def list_print_settings_specs(self, document_type=''):
        return self.list_template_specs(template_type=document_type)

    def get_default_template_spec(self, template_type):
        return None

    def get_default_print_settings_spec(self, document_type):
        return self.get_default_template_spec(template_type=document_type)

    def get_template_spec(self, template_id, template_type=''):
        return None

    def get_print_settings_spec(self, print_settings_id, document_type=''):
        return self.get_template_spec(
            template_id=print_settings_id,
            template_type=document_type,
        )


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
        template_repo = FakeDocumentTemplateRepository()
        use_case = GetWorkDetailUseCase(
            work_repo=FakeWorkRepository(
                variants=['variant-1'],
                analog_groups=[],
                spec_preview=['spec-1'],
            ),
            work_service=WorkService(),
            document_template_repo=template_repo,
        )

        result = use_case.execute('work-1')

        self.assertEqual(result.work.name, 'Контрольная')
        self.assertEqual(result.variants, ['variant-1'])
        self.assertEqual(result.spec_preview, ['spec-1'])
        self.assertEqual(
            result.work_print_settings[0].template_id,
            'template-work',
        )
        self.assertEqual(
            result.remedial_sheet_print_settings[0].template_id,
            'template-remedial',
        )
        self.assertEqual(
            result.work_document_templates[0].template_id,
            'template-work',
        )
        self.assertEqual(
            template_repo.requested_template_types,
            ['work', 'remedial_sheet'],
        )
        self.assertIn(
            WORK_DOCUMENT_STYLE_WORKSHEET,
            [option.value for option in result.work_document_style_options],
        )
        self.assertTrue(result.show_sync_button)

    def test_get_work_detail_use_case_returns_empty_data_for_missing_work(self):
        repo = FakeWorkRepository()
        use_case = GetWorkDetailUseCase(
            work_repo=repo,
            work_service=WorkService(),
        )

        result = use_case.execute('missing-work')

        self.assertIsNone(result.work)
        self.assertEqual(result.variants, [])

    def test_get_work_list_use_case_builds_list_context_data(self):
        repo = FakeWorkRepository()
        repo.works = FakeQuerySet(['work-1'])
        use_case = GetWorkListUseCase(work_repo=repo)

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
        use_case = GetWorkListUseCase(work_repo=repo)

        result = use_case.execute(filters)

        self.assertEqual(repo.work_list_filters, filters)
        self.assertEqual(result.filters, filters)

    def test_get_variant_list_use_case_builds_list_context_data(self):
        repo = FakeWorkRepository()
        repo.list_variants = FakeQuerySet(['variant-1'])
        use_case = GetVariantListUseCase(work_repo=repo)

        result = use_case.execute()

        self.assertEqual(result.variants, ['variant-1'])

    def test_get_work_form_data_use_case_builds_form_context_data(self):
        repo = FakeWorkRepository()
        repo.work_form_analog_group_options = ['group-1']
        use_case = GetWorkFormDataUseCase(work_repo=repo)

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
        use_case = GetVariantDetailUseCase(work_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(result.variant, repo.variant_detail)
        self.assertEqual(result.variant_tasks, repo.variant_detail_tasks)
        self.assertEqual(result.total_max_points, 7)

    def test_get_variant_detail_use_case_returns_empty_data_for_missing_variant(self):
        repo = FakeWorkRepository()
        use_case = GetVariantDetailUseCase(work_repo=repo)

        result = use_case.execute('missing-variant')

        self.assertIsNone(result.variant)
        self.assertEqual(result.variant_tasks, [])

    def test_get_variant_generation_placeholder_builds_message(self):
        repo = FakeWorkRepository()
        use_case = GetVariantGenerationPlaceholderUseCase(work_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(repo.variant_generation_id, 'variant-1')
        self.assertEqual(result.status, 'ready')
        self.assertEqual(
            result.message,
            'Вариант 3 работы "Контрольная" будет добавлен в следующей версии',
        )

    def test_get_variant_generation_placeholder_handles_missing_variant(self):
        repo = FakeWorkRepository()
        repo.variant_generation_info = None
        use_case = GetVariantGenerationPlaceholderUseCase(work_repo=repo)

        result = use_case.execute('missing')

        self.assertEqual(result.status, 'not_found')

    def test_get_remedial_sheet_data_use_case_returns_repository_data(self):
        repo = FakeWorkRepository()
        use_case = GetRemedialSheetDataUseCase(work_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(repo.variant_type_request, 'variant-1')
        self.assertEqual(repo.remedial_sheet_variant_id, 'variant-1')
        self.assertEqual(result, repo.remedial_sheet_data)

    def test_get_remedial_sheet_data_use_case_handles_missing_variant(self):
        repo = FakeWorkRepository()
        repo.variant_type = None
        use_case = GetRemedialSheetDataUseCase(work_repo=repo)

        result = use_case.execute('missing')

        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(result.variant)
        self.assertIsNone(repo.remedial_sheet_variant_id)

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
        use_case = GetOrphanVariantListUseCase(work_repo=repo)

        result = use_case.execute()

        self.assertEqual(result.variants, ['variant-1'])
        self.assertEqual(result.total_orphans, 1)

    def test_sync_work_analog_groups_use_case_delegates_to_repository(self):
        repo = FakeWorkRepository()
        use_case = SyncWorkAnalogGroupsUseCase(work_repo=repo)

        result = use_case.execute(SyncWorkAnalogGroupsRequest(work_id='work-1'))

        self.assertEqual(result.status, 'synced')
        self.assertEqual(result.created_count, 2)
        self.assertEqual(repo.work_name_request, 'work-1')
        self.assertEqual(repo.synced_work_id, 'work-1')

    def test_sync_work_analog_groups_use_case_handles_missing_work(self):
        repo = FakeWorkRepository()
        repo.work_name = None
        use_case = SyncWorkAnalogGroupsUseCase(work_repo=repo)

        result = use_case.execute(SyncWorkAnalogGroupsRequest(work_id='missing'))

        self.assertEqual(result.status, 'not_found')
        self.assertEqual(result.created_count, 0)
        self.assertIsNone(repo.synced_work_id)

    def test_compose_work_variants_use_case_delegates_to_repository(self):
        repo = FakeWorkRepository()
        use_case = ComposeWorkVariantsUseCase(work_repo=repo)

        result = use_case.execute(
            ComposeWorkVariantsRequest(work_id='work-1', count=3)
        )

        self.assertEqual(result.status, 'generated')
        self.assertEqual(result.created_count, 3)
        self.assertEqual(repo.work_name_request, 'work-1')
        self.assertEqual(repo.generated_variants_request, ('work-1', 3))

    def test_compose_work_variants_use_case_handles_missing_work(self):
        repo = FakeWorkRepository()
        repo.work_name = None
        use_case = ComposeWorkVariantsUseCase(work_repo=repo)

        result = use_case.execute(
            ComposeWorkVariantsRequest(work_id='missing', count=3)
        )

        self.assertEqual(result.status, 'not_found')
        self.assertEqual(result.created_count, 0)
        self.assertIsNone(repo.generated_variants_request)

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

    def test_get_variant_delete_info_use_case_delegates_to_repository(self):
        repo = FakeWorkRepository()
        repo.variant_delete_info = VariantDeleteInfo(
            task_count=3,
            participation_count=1,
        )
        use_case = GetVariantDeleteInfoUseCase(work_repo=repo)

        result = use_case.execute('variant-1')

        self.assertEqual(result.task_count, 3)
        self.assertTrue(result.has_participations)

    def test_get_variant_delete_info_use_case_returns_none_for_missing_variant(self):
        repo = FakeWorkRepository()
        repo.variant_delete_info = None
        use_case = GetVariantDeleteInfoUseCase(work_repo=repo)

        result = use_case.execute('missing-variant')

        self.assertIsNone(result)

    def test_delete_variant_use_case_returns_not_found_for_missing_variant(self):
        repo = FakeWorkRepository()
        repo.variant_delete_info = None
        use_case = DeleteVariantUseCase(work_repo=repo)

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
        use_case = DeleteVariantUseCase(work_repo=repo)

        result = use_case.execute(
            DeleteVariantRequest(variant_id='variant-1', action='delete')
        )

        self.assertEqual(result.status, 'blocked_has_participations')
        self.assertEqual(result.participation_count, 1)
        self.assertIsNone(repo.deleted_variant_id)

    def test_delete_variant_use_case_detaches_variant(self):
        repo = FakeWorkRepository()
        use_case = DeleteVariantUseCase(work_repo=repo)

        result = use_case.execute(
            DeleteVariantRequest(variant_id='variant-1', action='detach')
        )

        self.assertEqual(result.status, 'detached')
        self.assertEqual(result.variant_short_id, 'ABCD')
        self.assertEqual(repo.detached_variant_id, 'variant-1')

    def test_delete_variant_use_case_deletes_variant_without_participations(self):
        repo = FakeWorkRepository()
        use_case = DeleteVariantUseCase(work_repo=repo)

        result = use_case.execute(
            DeleteVariantRequest(variant_id='variant-1', action='delete')
        )

        self.assertEqual(result.status, 'deleted')
        self.assertEqual(result.redirect_work_id, 'work-1')
        self.assertEqual(repo.deleted_variant_id, 'variant-1')

    def test_bulk_delete_variants_use_case_deletes_selected_variants(self):
        repo = FakeWorkRepository()
        repo.remaining_variant_count = 4
        use_case = BulkDeleteVariantsUseCase(work_repo=repo)

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
        use_case = BulkDeleteVariantsUseCase(work_repo=repo)

        result = use_case.execute(
            BulkDeleteVariantsRequest(work_id='work-1', variant_ids=[])
        )

        self.assertEqual(result.status, 'empty_selection')
        self.assertIsNone(repo.bulk_deleted_request)
