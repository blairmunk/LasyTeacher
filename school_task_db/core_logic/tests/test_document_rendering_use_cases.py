"""Document rendering use case tests."""

from unittest import TestCase

from core_logic.entities.document import (
    DocumentPresentation,
    DocumentSectionSpec,
    PrintSettingsSpec,
)
from core_logic.entities.document_rendering import (
    DocumentRenderResult,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    GeneratedDocument,
    GeneratedDocumentFile,
    GeneratedFile,
    GeneratedFileResult,
)
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileRequest,
    GetRenderedDocumentFileUseCase,
)
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.render_remedial_sheet_batch_document import (
    RenderRemedialSheetBatchDocumentRequest,
    RenderRemedialSheetBatchDocumentUseCase,
)
from core_logic.use_cases.render_work_document import (
    RenderWorkDocumentRequest,
    RenderWorkDocumentUseCase,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    HEADER_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
)


class FakeDocumentEngine:
    def __init__(self):
        self.render_request = None
        self.work_document = GeneratedDocument(
            file_type='html',
            files=[GeneratedDocumentFile(filename='work.html', size_kb=1.0)],
        )
        self.remedial_document = GeneratedDocument(
            file_type='pdf',
            files=[GeneratedDocumentFile(filename='remedial.pdf', size_kb=2.0)],
        )
        self.file_request = None
        self.file_result = GeneratedFileResult(
            status='ready',
            file=GeneratedFile(
                filename='work.html',
                content=b'html',
                content_type='text/html',
            ),
        )

    def render_document(self, render_plan):
        self.render_request = render_plan
        if render_plan.recipe.document_type == 'remedial_sheet':
            return self.remedial_document
        return self.work_document

    def get_rendered_file(self, file_type, filename):
        self.file_request = (file_type, filename)
        return self.file_result


class FakeWorkRepository:
    def __init__(
        self,
        variant_type='remedial',
        work_name='Контрольная',
        variant_ids=None,
        remedial_variant_ids=None,
    ):
        self.variant_type = variant_type
        self.variant_type_request = None
        self.work_name = work_name
        self.work_name_request = None
        self.remedial_variant_ids = remedial_variant_ids or []
        self.remedial_variant_ids_request = None
        self.variant_ids = variant_ids or ['variant-1']
        self.variant_ids_request = None

    def get_work_name(self, work_id):
        self.work_name_request = work_id
        return self.work_name

    def get_variant_type(self, variant_id):
        self.variant_type_request = variant_id
        return self.variant_type

    def get_work_remedial_variant_ids(self, work_id):
        self.remedial_variant_ids_request = work_id
        return self.remedial_variant_ids

    def get_work_variant_ids(self, work_id):
        self.variant_ids_request = work_id
        return self.variant_ids


class FakeRenderRemedialSheetDocumentUseCase:
    def __init__(self):
        self.requests = []
        self.results_by_variant_id = {}

    def execute(self, request):
        self.requests.append(request)
        return self.results_by_variant_id.get(
            request.variant_id,
            DocumentRenderResult(
                status='generated',
                renderer_type=request.options.renderer_type,
                file_type=request.options.renderer_type,
                files=[
                    GeneratedDocumentFile(
                        filename=f'remedial_{request.variant_id}.pdf',
                        size_kb=2.0,
                    ),
                ],
            ),
        )


class FakePrintSettingsRepository:
    def __init__(self):
        self.requested_document_types = []
        self.requested_print_settings_ids = []
        self.default_print_settings = {}
        self.print_settings_by_id = {}

    def list_print_settings_specs(self, document_type=''):
        return []

    def get_default_print_settings_spec(self, document_type):
        self.requested_document_types.append(document_type)
        return self.default_print_settings.get(document_type)

    def get_print_settings_spec(self, print_settings_id, document_type=''):
        self.requested_print_settings_ids.append(
            (print_settings_id, document_type),
        )
        return self.print_settings_by_id.get(
            (print_settings_id, document_type),
        )


class DocumentRenderingUseCaseTests(TestCase):
    def test_document_render_result_exposes_renderer_type(self):
        result = DocumentRenderResult(status='generated', renderer_type='html')

        self.assertEqual(result.renderer_type, 'html')

    def test_render_work_document_rejects_unsupported_renderer(self):
        service = FakeDocumentEngine()
        work_repo = FakeWorkRepository()
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=work_repo,
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='docx'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER)
        self.assertEqual(result.renderer_type, 'docx')
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertEqual(work_repo.work_name_request, 'work-1')
        self.assertIsNone(service.render_request)

    def test_render_work_document_delegates_to_service(self):
        service = FakeDocumentEngine()
        work_repo = FakeWorkRepository()
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=work_repo,
        )
        options = WorkDocumentRenderOptions(renderer_type='html')

        result = use_case.execute(
            RenderWorkDocumentRequest(work_id='work-1', options=options)
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(result.files[0].filename, 'work.html')
        self.assertEqual(result.files[0].size_kb, 1.0)
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertEqual(work_repo.work_name_request, 'work-1')
        render_plan = service.render_request
        self.assertEqual(render_plan.source.source_type, 'work')
        self.assertEqual(render_plan.source.source_id, 'work-1')
        self.assertEqual(render_plan.source.title, 'Контрольная')
        self.assertEqual(render_plan.render_target.renderer_type, 'html')
        self.assertEqual(
            render_plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )

    def test_render_work_document_accepts_document_engine_keyword(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.render_request.source.source_id, 'work-1')

    def test_render_work_document_uses_request_print_settings_spec(self):
        service = FakeDocumentEngine()
        print_settings_repo = FakePrintSettingsRepository()
        print_settings_repo.default_print_settings['work'] = PrintSettingsSpec(
            name='Default work',
            document_type='work',
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            print_settings_repo=print_settings_repo,
        )
        self.assertIs(use_case.print_settings_repo, print_settings_repo)
        print_settings_spec = PrintSettingsSpec(
            name='Кастомная работа',
            document_type='work',
            sections=[
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
                DocumentSectionSpec(section_type=ANSWERS_SECTION),
            ],
            presentation=DocumentPresentation(
                custom_latex_preamble='\\usepackage{multicol}',
            ),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='html'),
                print_settings_spec=print_settings_spec,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(print_settings_repo.requested_document_types, [])
        render_plan = service.render_request
        self.assertEqual(
            render_plan.recipe.section_types,
            (TASK_LIST_SECTION, ANSWERS_SECTION),
        )
        self.assertEqual(
            render_plan.recipe.presentation.custom_latex_preamble,
            '\\usepackage{multicol}',
        )

    def test_render_work_document_uses_request_print_settings_spec(self):
        service = FakeDocumentEngine()
        print_settings_repo = FakePrintSettingsRepository()
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            print_settings_repo=print_settings_repo,
        )
        print_settings_spec = PrintSettingsSpec(
            name='Профиль печати',
            document_type='work',
            sections=[DocumentSectionSpec(section_type=ANSWERS_SECTION)],
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='html'),
                print_settings_spec=print_settings_spec,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(print_settings_repo.requested_document_types, [])
        self.assertEqual(service.render_request.recipe.section_types, (ANSWERS_SECTION,))

    def test_render_work_document_uses_default_print_settings_spec(self):
        service = FakeDocumentEngine()
        print_settings_repo = FakePrintSettingsRepository()
        print_settings_repo.default_print_settings['work'] = PrintSettingsSpec(
            name='Default work',
            document_type='work',
            sections=[DocumentSectionSpec(section_type=TASK_LIST_SECTION)],
        )
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            print_settings_repo=print_settings_repo,
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(print_settings_repo.requested_document_types, ['work'])
        render_plan = service.render_request
        self.assertEqual(render_plan.recipe.section_types, (TASK_LIST_SECTION,))

    def test_render_work_document_uses_print_settings_id(self):
        service = FakeDocumentEngine()
        print_settings_repo = FakePrintSettingsRepository()
        print_settings_repo.print_settings_by_id[('template-work', 'work')] = (
            PrintSettingsSpec(
                name='Selected work',
                document_type='work',
                print_settings_id='template-work',
                sections=[DocumentSectionSpec(section_type=ANSWERS_SECTION)],
            )
        )
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            print_settings_repo=print_settings_repo,
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='html'),
                print_settings_id='template-work',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            print_settings_repo.requested_print_settings_ids,
            [('template-work', 'work')],
        )
        self.assertEqual(service.render_request.recipe.section_types, (ANSWERS_SECTION,))

    def test_render_work_document_handles_missing_work(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(work_name=None),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='missing-work',
                options=WorkDocumentRenderOptions(renderer_type='html'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(service.render_request)

    def test_render_work_document_can_select_one_work_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(
                variant_ids=['variant-1', 'variant-2'],
            ),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                variant_id='variant-2',
                options=WorkDocumentRenderOptions(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            [
                section.options.get('variant_id')
                for section in service.render_request.recipe.sections
            ],
            ['variant-2', 'variant-2'],
        )

    def test_render_work_document_rejects_foreign_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(variant_ids=['variant-1']),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                variant_id='foreign-variant',
                options=WorkDocumentRenderOptions(renderer_type='html'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_document_delegates_to_service(self):
        service = FakeDocumentEngine()
        work_repo = FakeWorkRepository()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=work_repo,
        )
        options = RemedialSheetDocumentRenderOptions(renderer_type='pdf')

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=options,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(result.files[0].filename, 'remedial.pdf')
        self.assertEqual(result.files[0].size_kb, 2.0)
        self.assertEqual(work_repo.variant_type_request, 'variant-1')
        render_plan = service.render_request
        self.assertEqual(render_plan.source.source_type, 'remedial_variant')
        self.assertEqual(render_plan.source.source_id, 'variant-1')
        self.assertEqual(render_plan.render_target.renderer_type, 'pdf')
        self.assertEqual(
            render_plan.recipe.section_types,
            (
                HEADER_SECTION,
                'original_mistakes',
                'training_tasks',
                ANSWERS_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )

    def test_render_remedial_sheet_document_accepts_document_engine_keyword(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.render_request.source.source_id, 'variant-1')

    def test_render_remedial_sheet_document_uses_request_print_settings_spec(self):
        service = FakeDocumentEngine()
        print_settings_repo = FakePrintSettingsRepository()
        print_settings_repo.default_print_settings['remedial_sheet'] = PrintSettingsSpec(
            name='Default remedial',
            document_type='remedial_sheet',
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            print_settings_repo=print_settings_repo,
        )
        print_settings_spec = PrintSettingsSpec(
            name='Кастомная работа над ошибками',
            document_type='remedial_sheet',
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
            ],
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
                print_settings_spec=print_settings_spec,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(print_settings_repo.requested_document_types, [])
        render_plan = service.render_request
        self.assertEqual(
            render_plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )

    def test_render_remedial_sheet_document_uses_default_print_settings_spec(self):
        service = FakeDocumentEngine()
        print_settings_repo = FakePrintSettingsRepository()
        print_settings_repo.default_print_settings['remedial_sheet'] = PrintSettingsSpec(
            name='Default remedial',
            document_type='remedial_sheet',
            sections=[DocumentSectionSpec(section_type=TASK_LIST_SECTION)],
        )
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            print_settings_repo=print_settings_repo,
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            print_settings_repo.requested_document_types,
            ['remedial_sheet'],
        )
        render_plan = service.render_request
        self.assertEqual(render_plan.recipe.section_types, (TASK_LIST_SECTION,))

    def test_render_remedial_sheet_document_uses_selected_print_settings_id(
        self,
    ):
        service = FakeDocumentEngine()
        print_settings_repo = FakePrintSettingsRepository()
        print_settings_repo.print_settings_by_id[('template-rno', 'remedial_sheet')] = (
            PrintSettingsSpec(
                name='Selected remedial',
                document_type='remedial_sheet',
                print_settings_id='template-rno',
                sections=[DocumentSectionSpec(section_type=ANSWERS_SECTION)],
            )
        )
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            print_settings_repo=print_settings_repo,
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
                print_settings_id='template-rno',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            print_settings_repo.requested_print_settings_ids,
            [('template-rno', 'remedial_sheet')],
        )
        self.assertEqual(service.render_request.recipe.section_types, (ANSWERS_SECTION,))

    def test_render_remedial_sheet_document_uses_print_settings_id(self):
        service = FakeDocumentEngine()
        print_settings_repo = FakePrintSettingsRepository()
        print_settings_repo.print_settings_by_id[('profile-rno', 'remedial_sheet')] = (
            PrintSettingsSpec(
                name='Selected remedial',
                document_type='remedial_sheet',
                print_settings_id='profile-rno',
                sections=[DocumentSectionSpec(section_type=ANSWERS_SECTION)],
            )
        )
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            print_settings_repo=print_settings_repo,
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
                print_settings_id='profile-rno',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            print_settings_repo.requested_print_settings_ids,
            [('profile-rno', 'remedial_sheet')],
        )
        self.assertEqual(service.render_request.recipe.section_types, (ANSWERS_SECTION,))

    def test_render_remedial_sheet_document_handles_empty_files(self):
        service = FakeDocumentEngine()
        service.remedial_document = GeneratedDocument(file_type='pdf')
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty')

    def test_render_remedial_sheet_document_rejects_unsupported_renderer(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='docx'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER)
        self.assertEqual(result.renderer_type, 'docx')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_document_rejects_non_remedial_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(variant_type='regular'),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_remedial')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_document_handles_missing_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(variant_type=None),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_batch_document_builds_one_batch_plan(self):
        work_repo = FakeWorkRepository(
            work_name='Работа над ошибками',
            remedial_variant_ids=['variant-1', 'variant-2'],
        )
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            document_engine=service,
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='work-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(result.source_name, 'Работа над ошибками')
        self.assertEqual(work_repo.work_name_request, 'work-1')
        self.assertEqual(work_repo.remedial_variant_ids_request, 'work-1')
        self.assertEqual(result.files[0].filename, 'remedial.pdf')
        render_plan = service.render_request
        self.assertEqual(render_plan.source.source_type, 'remedial_work')
        self.assertEqual(render_plan.source.source_id, 'work-1')
        self.assertEqual(
            render_plan.recipe.section_types,
            (
                HEADER_SECTION,
                'original_mistakes',
                'training_tasks',
                ANSWERS_SECTION,
                SHORT_SOLUTIONS_SECTION,
                'page_break',
                HEADER_SECTION,
                'original_mistakes',
                'training_tasks',
                ANSWERS_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )
        self.assertEqual(
            [
                section.options.get('variant_id')
                for section in render_plan.recipe.sections
                if section.section_type != 'page_break'
            ],
            [
                'variant-1',
                'variant-1',
                'variant-1',
                'variant-1',
                'variant-1',
                'variant-2',
                'variant-2',
                'variant-2',
                'variant-2',
                'variant-2',
            ],
        )

    def test_render_remedial_sheet_batch_document_uses_print_settings_spec(self):
        work_repo = FakeWorkRepository(
            work_name='Работа над ошибками',
            remedial_variant_ids=['variant-1'],
        )
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            document_engine=service,
        )
        print_settings_spec = PrintSettingsSpec(
            name='Профиль РнО',
            document_type='remedial_sheet',
            sections=[DocumentSectionSpec(section_type=ANSWERS_SECTION)],
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='work-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
                print_settings_spec=print_settings_spec,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.render_request.recipe.section_types, (ANSWERS_SECTION,))

    def test_render_remedial_sheet_batch_document_handles_missing_work(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=FakeWorkRepository(work_name=None),
            document_engine=service,
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='missing-work',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_batch_document_handles_empty_work(self):
        work_repo = FakeWorkRepository(
            work_name='Работа над ошибками',
            remedial_variant_ids=[],
        )
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            document_engine=service,
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='work-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty')
        self.assertEqual(result.source_name, 'Работа над ошибками')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_batch_document_handles_empty_rendered_file(self):
        work_repo = FakeWorkRepository(
            work_name='Работа над ошибками',
            remedial_variant_ids=['variant-1', 'variant-2'],
        )
        service = FakeDocumentEngine()
        service.remedial_document = GeneratedDocument(file_type='pdf')
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            document_engine=service,
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='work-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty')
        self.assertEqual(result.files, [])

    def test_get_rendered_document_file_delegates_to_service(self):
        service = FakeDocumentEngine()
        use_case = GetRenderedDocumentFileUseCase(
            document_engine=service,
        )

        result = use_case.execute(
            GetRenderedDocumentFileRequest(
                file_type='html',
                filename='work.html',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file.content, b'html')
        self.assertEqual(service.file_request, ('html', 'work.html'))

    def test_get_rendered_document_file_requires_document_engine(self):
        with self.assertRaisesRegex(
            ValueError,
            'Document engine dependency is required.',
        ):
            GetRenderedDocumentFileUseCase()

    def test_get_rendered_document_file_accepts_document_engine_keyword(self):
        service = FakeDocumentEngine()
        use_case = GetRenderedDocumentFileUseCase(document_engine=service)

        result = use_case.execute(
            GetRenderedDocumentFileRequest(
                file_type='html',
                filename='work.html',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.file_request, ('html', 'work.html'))
