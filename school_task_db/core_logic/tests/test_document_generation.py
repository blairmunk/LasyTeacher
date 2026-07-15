from unittest import TestCase

from core_logic.entities.document_generation import GeneratedDocument
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

    def generate_work(self, work, options):
        self.work_request = (work, options)
        return self.work_document

    def generate_remedial_sheet(self, variant, options):
        self.remedial_request = (variant, options)
        return self.remedial_document


class DocumentGenerationUseCaseTests(TestCase):
    def test_generate_work_document_rejects_unsupported_generator(self):
        service = FakeDocumentGenerationService()
        use_case = GenerateWorkDocumentUseCase(
            document_generation_service=service,
        )

        result = use_case.execute(
            GenerateWorkDocumentRequest(
                work='work',
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
            GenerateWorkDocumentRequest(work='work', options=options)
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(result.file_paths, ['work.html'])
        self.assertEqual(service.work_request, ('work', options))

    def test_generate_remedial_sheet_document_delegates_to_service(self):
        service = FakeDocumentGenerationService()
        use_case = GenerateRemedialSheetDocumentUseCase(
            document_generation_service=service,
        )
        options = RemedialSheetGenerationOptions(generator_type='pdf')

        result = use_case.execute(
            GenerateRemedialSheetDocumentRequest(
                variant='variant',
                options=options,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(result.file_paths, ['remedial.pdf'])
        self.assertEqual(service.remedial_request, ('variant', options))

    def test_generate_remedial_sheet_document_handles_empty_files(self):
        service = FakeDocumentGenerationService()
        service.remedial_document = GeneratedDocument(file_type='pdf')
        use_case = GenerateRemedialSheetDocumentUseCase(
            document_generation_service=service,
        )

        result = use_case.execute(
            GenerateRemedialSheetDocumentRequest(
                variant='variant',
                options=RemedialSheetGenerationOptions(),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty')
