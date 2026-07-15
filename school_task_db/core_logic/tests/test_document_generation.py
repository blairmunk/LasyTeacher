from unittest import TestCase

from core_logic.entities.document_generation import (
    GeneratedDocument,
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
from core_logic.use_cases.generate_work_document import (
    GenerateWorkDocumentRequest,
    GenerateWorkDocumentUseCase,
)
from core_logic.value_objects.content_config import (
    RemedialSheetGenerationOptions,
    WorkGenerationOptions,
)


class FakeDocumentGenerationService:
    def __init__(self):
        self.work_request = None
        self.remedial_request = None
        self.work_document = GeneratedDocument(
            file_type='html',
            file_paths=['work.html'],
        )
        self.remedial_document = GeneratedDocument(
            file_type='pdf',
            file_paths=['remedial.pdf'],
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

    def generate_work(self, work_id, options):
        self.work_request = (work_id, options)
        return self.work_document

    def generate_remedial_sheet(self, variant_id, options):
        self.remedial_request = (variant_id, options)
        return self.remedial_document

    def get_generated_file(self, file_type, filename):
        self.file_request = (file_type, filename)
        return self.file_result


class DocumentGenerationUseCaseTests(TestCase):
    def test_generate_work_document_rejects_unsupported_generator(self):
        service = FakeDocumentGenerationService()
        use_case = GenerateWorkDocumentUseCase(
            document_generation_service=service,
        )

        result = use_case.execute(
            GenerateWorkDocumentRequest(
                work_id='work-1',
                options=WorkGenerationOptions(generator_type='docx'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'unsupported_generator')
        self.assertEqual(result.generator_type, 'docx')
        self.assertIsNone(service.work_request)

    def test_generate_work_document_delegates_to_service(self):
        service = FakeDocumentGenerationService()
        use_case = GenerateWorkDocumentUseCase(
            document_generation_service=service,
        )
        options = WorkGenerationOptions(generator_type='html')

        result = use_case.execute(
            GenerateWorkDocumentRequest(work_id='work-1', options=options)
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(result.file_paths, ['work.html'])
        self.assertEqual(service.work_request, ('work-1', options))

    def test_generate_remedial_sheet_document_delegates_to_service(self):
        service = FakeDocumentGenerationService()
        use_case = GenerateRemedialSheetDocumentUseCase(
            document_generation_service=service,
        )
        options = RemedialSheetGenerationOptions(generator_type='pdf')

        result = use_case.execute(
            GenerateRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=options,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(result.file_paths, ['remedial.pdf'])
        self.assertEqual(service.remedial_request, ('variant-1', options))

    def test_generate_remedial_sheet_document_handles_empty_files(self):
        service = FakeDocumentGenerationService()
        service.remedial_document = GeneratedDocument(file_type='pdf')
        use_case = GenerateRemedialSheetDocumentUseCase(
            document_generation_service=service,
        )

        result = use_case.execute(
            GenerateRemedialSheetDocumentRequest(
                variant_id='variant-1',
                options=RemedialSheetGenerationOptions(),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty')

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
