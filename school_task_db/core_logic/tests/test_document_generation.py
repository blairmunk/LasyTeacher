from unittest import TestCase

from core_logic.entities.document_generation import (
    DocumentGenerationResult,
    DocumentRenderResult,
    GeneratedDocument,
    GeneratedDocumentFile,
    GeneratedFile,
    GeneratedFileResult,
)
from core_logic.use_cases.get_generated_document_file import (
    GetGeneratedDocumentFileRequest,
    GetGeneratedDocumentFileUseCase,
)
from core_logic.use_cases.generate_remedial_sheet_document import (
    GenerateRemedialSheetDocumentRequest,
    GenerateRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.generate_work_document import (
    GenerateWorkDocumentRequest,
    GenerateWorkDocumentUseCase,
)
from core_logic.use_cases.render_work_document import (
    RenderWorkDocumentRequest,
    RenderWorkDocumentUseCase,
)
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    RemedialSheetGenerationOptions,
    WorkDocumentRenderOptions,
    WorkGenerationOptions,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    HEADER_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_VARIANTS_SECTION,
)


class FakeDocumentGenerationService:
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

    def generate_work(self, work_id, options, render_plan=None):
        return self.render_work_document(work_id, options, render_plan)

    def render_remedial_sheet_document(self, variant_id, options, render_plan=None):
        self.remedial_request = (variant_id, options, render_plan)
        return self.remedial_document

    def generate_remedial_sheet(self, variant_id, options, render_plan=None):
        return self.render_remedial_sheet_document(
            variant_id,
            options,
            render_plan,
        )

    def get_generated_file(self, file_type, filename):
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


class DocumentGenerationUseCaseTests(TestCase):
    def test_document_generation_result_aliases_document_render_result(self):
        result = DocumentGenerationResult(status='generated', renderer_type='html')

        self.assertIsInstance(result, DocumentRenderResult)
        self.assertEqual(result.generator_type, 'html')

    def test_render_work_document_rejects_unsupported_renderer(self):
        service = FakeDocumentGenerationService()
        work_repo = FakeWorkRepository()
        use_case = RenderWorkDocumentUseCase(
            document_generation_service=service,
            work_repo=work_repo,
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                options=WorkDocumentRenderOptions(renderer_type='docx'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'unsupported_generator')
        self.assertEqual(result.generator_type, 'docx')
        self.assertEqual(result.renderer_type, 'docx')
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertEqual(work_repo.work_name_request, 'work-1')
        self.assertIsNone(service.work_request)

    def test_render_work_document_delegates_to_service(self):
        service = FakeDocumentGenerationService()
        work_repo = FakeWorkRepository()
        use_case = RenderWorkDocumentUseCase(
            document_generation_service=service,
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

    def test_render_work_document_handles_missing_work(self):
        service = FakeDocumentGenerationService()
        use_case = RenderWorkDocumentUseCase(
            document_generation_service=service,
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

    def test_legacy_generate_work_document_use_case_alias(self):
        service = FakeDocumentGenerationService()
        work_repo = FakeWorkRepository()
        use_case = GenerateWorkDocumentUseCase(
            document_generation_service=service,
            work_repo=work_repo,
        )

        result = use_case.execute(
            GenerateWorkDocumentRequest(
                work_id='work-1',
                options=WorkGenerationOptions(generator_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.work_request[0], 'work-1')

    def test_render_remedial_sheet_document_delegates_to_service(self):
        service = FakeDocumentGenerationService()
        work_repo = FakeWorkRepository()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_generation_service=service,
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

    def test_render_remedial_sheet_document_handles_empty_files(self):
        service = FakeDocumentGenerationService()
        service.remedial_document = GeneratedDocument(file_type='pdf')
        use_case = RenderRemedialSheetDocumentUseCase(
            document_generation_service=service,
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
        service = FakeDocumentGenerationService()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_generation_service=service,
            work_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetDocumentRenderOptions(renderer_type='docx'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'unsupported_generator')
        self.assertEqual(result.generator_type, 'docx')
        self.assertEqual(result.renderer_type, 'docx')
        self.assertIsNone(service.remedial_request)

    def test_render_remedial_sheet_document_rejects_non_remedial_variant(self):
        service = FakeDocumentGenerationService()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_generation_service=service,
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
        service = FakeDocumentGenerationService()
        use_case = RenderRemedialSheetDocumentUseCase(
            document_generation_service=service,
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

    def test_legacy_generate_remedial_sheet_document_use_case_alias(self):
        service = FakeDocumentGenerationService()
        work_repo = FakeWorkRepository()
        use_case = GenerateRemedialSheetDocumentUseCase(
            document_generation_service=service,
            work_repo=work_repo,
        )

        result = use_case.execute(
            GenerateRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetGenerationOptions(generator_type='pdf'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.remedial_request[0], 'variant-1')

    def test_get_generated_document_file_delegates_to_service(self):
        service = FakeDocumentGenerationService()
        use_case = GetGeneratedDocumentFileUseCase(
            document_generation_service=service,
        )

        result = use_case.execute(
            GetGeneratedDocumentFileRequest(
                file_type='html',
                filename='work.html',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file.content, b'html')
        self.assertEqual(service.file_request, ('html', 'work.html'))
