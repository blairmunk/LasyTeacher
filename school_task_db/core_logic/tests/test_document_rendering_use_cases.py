"""Document rendering use case tests."""

from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    DocumentTemplateSpec,
)
from core_logic.entities.document_rendering import (
    DocumentRenderResult,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    GeneratedDocument,
    GeneratedDocumentFile,
    GeneratedFile,
    GeneratedFileResult,
)
from core_logic.use_cases.document_engine_dependency import resolve_document_engine
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileRequest,
    GetRenderedDocumentFileUseCase,
)
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.render_work_document import (
    RenderWorkDocumentRequest,
    RenderWorkDocumentUseCase,
)
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    HEADER_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TASK_VARIANTS_SECTION,
)


class FakeDocumentEngine:
    def __init__(self):
        self.work_request = None
        self.remedial_request = None
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

    def render_work_document(self, work_id, options, render_plan=None):
        self.work_request = (work_id, options, render_plan)
        return self.work_document

    def render_remedial_sheet_document(self, variant_id, options, render_plan=None):
        self.remedial_request = (variant_id, options, render_plan)
        return self.remedial_document

    def get_rendered_file(self, file_type, filename):
        self.file_request = (file_type, filename)
        return self.file_result


class FakeWorkRepository:
    def __init__(self, variant_type='remedial', work_name='Контрольная'):
        self.variant_type = variant_type
        self.variant_type_request = None
        self.work_name = work_name
        self.work_name_request = None

    def get_work_name(self, work_id):
        self.work_name_request = work_id
        return self.work_name

    def get_variant_type(self, variant_id):
        self.variant_type_request = variant_id
        return self.variant_type


class FakeDocumentTemplateRepository:
    def __init__(self):
        self.requested_template_types = []
        self.default_templates = {}

    def list_template_specs(self, template_type=''):
        return []

    def get_default_template_spec(self, template_type):
        self.requested_template_types.append(template_type)
        return self.default_templates.get(template_type)


class DocumentRenderingUseCaseTests(TestCase):
    def test_resolve_document_engine_prefers_engine_keyword(self):
        document_engine = FakeDocumentEngine()

        result = resolve_document_engine(
            document_engine=document_engine,
        )

        self.assertIs(result, document_engine)

    def test_resolve_document_engine_requires_dependency(self):
        with self.assertRaisesRegex(
            ValueError,
            'Document engine dependency is required.',
        ):
            resolve_document_engine()

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
        self.assertIsNone(service.work_request)

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
        work_id, used_options, render_plan = service.work_request
        self.assertEqual(work_id, 'work-1')
        self.assertEqual(used_options, options)
        self.assertEqual(render_plan.source.source_type, 'work')
        self.assertEqual(render_plan.source.source_id, 'work-1')
        self.assertEqual(render_plan.source.title, 'Контрольная')
        self.assertEqual(render_plan.render_target.renderer_type, 'html')
        self.assertEqual(
            render_plan.recipe.section_types,
            (HEADER_SECTION, TASK_VARIANTS_SECTION),
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
        self.assertEqual(service.work_request[0], 'work-1')

    def test_render_work_document_uses_request_template_spec(self):
        service = FakeDocumentEngine()
        template_repo = FakeDocumentTemplateRepository()
        template_repo.default_templates['work'] = DocumentTemplateSpec(
            name='Default work',
            template_type='work',
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            document_template_repo=template_repo,
        )
        template_spec = DocumentTemplateSpec(
            name='Кастомная работа',
            template_type='work',
            sections=[
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
                DocumentSectionSpec(section_type=ANSWER_KEY_SECTION),
            ],
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='html'),
                template_spec=template_spec,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(template_repo.requested_template_types, [])
        render_plan = service.work_request[2]
        self.assertEqual(
            render_plan.recipe.section_types,
            (TASK_LIST_SECTION, ANSWER_KEY_SECTION),
        )

    def test_render_work_document_uses_default_template_spec(self):
        service = FakeDocumentEngine()
        template_repo = FakeDocumentTemplateRepository()
        template_repo.default_templates['work'] = DocumentTemplateSpec(
            name='Default work',
            template_type='work',
            sections=[DocumentSectionSpec(section_type=TASK_LIST_SECTION)],
        )
        use_case = RenderWorkDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            document_template_repo=template_repo,
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(template_repo.requested_template_types, ['work'])
        render_plan = service.work_request[2]
        self.assertEqual(render_plan.recipe.section_types, (TASK_LIST_SECTION,))

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
        self.assertIsNone(service.work_request)

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
        variant_id, used_options, render_plan = service.remedial_request
        self.assertEqual(variant_id, 'variant-1')
        self.assertEqual(used_options, options)
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
        self.assertEqual(service.remedial_request[0], 'variant-1')

    def test_render_remedial_sheet_document_uses_request_template_spec(self):
        service = FakeDocumentEngine()
        template_repo = FakeDocumentTemplateRepository()
        template_repo.default_templates['remedial_sheet'] = DocumentTemplateSpec(
            name='Default remedial',
            template_type='remedial_sheet',
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            document_template_repo=template_repo,
        )
        template_spec = DocumentTemplateSpec(
            name='Кастомная работа над ошибками',
            template_type='remedial_sheet',
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
            ],
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
                template_spec=template_spec,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(template_repo.requested_template_types, [])
        render_plan = service.remedial_request[2]
        self.assertEqual(
            render_plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )

    def test_render_remedial_sheet_document_uses_default_template_spec(self):
        service = FakeDocumentEngine()
        template_repo = FakeDocumentTemplateRepository()
        template_repo.default_templates['remedial_sheet'] = DocumentTemplateSpec(
            name='Default remedial',
            template_type='remedial_sheet',
            sections=[DocumentSectionSpec(section_type=TASK_LIST_SECTION)],
        )
        use_case = RenderRemedialSheetDocumentUseCase(
            document_engine=service,
            work_repo=FakeWorkRepository(),
            document_template_repo=template_repo,
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            template_repo.requested_template_types,
            ['remedial_sheet'],
        )
        render_plan = service.remedial_request[2]
        self.assertEqual(render_plan.recipe.section_types, (TASK_LIST_SECTION,))

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
        self.assertIsNone(service.remedial_request)

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
        self.assertIsNone(service.remedial_request)

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
        self.assertIsNone(service.remedial_request)

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
