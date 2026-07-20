from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
    GeneratedDocumentFile,
)
from infrastructure.services.html_to_pdf_generator import (
    HtmlToPdfGenerator as InfrastructureHtmlToPdfGenerator,
)
from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator


class HtmlToPdfGeneratorCompatibilityTests(SimpleTestCase):
    def test_legacy_import_path_reexports_infrastructure_backend(self):
        self.assertIs(HtmlToPdfGenerator, InfrastructureHtmlToPdfGenerator)


class GeneratePdfCommandTests(SimpleTestCase):
    def test_command_renders_work_pdf_through_container(self):
        use_case = FakeRenderWorkDocumentUseCase(
            result=DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_GENERATED,
                renderer_type='pdf',
                file_type='pdf',
                files=[
                    GeneratedDocumentFile(
                        filename='work_1.pdf',
                        size_kb=2.5,
                    ),
                ],
                source_name='Контрольная',
            ),
        )
        stdout = StringIO()

        with patch(
            'pdf_generator.management.commands.generate_pdf.container',
            FakeDocumentRenderContainer(use_case),
        ):
            call_command(
                'generate_pdf',
                'work',
                'work-1',
                '--format',
                'A5',
                '--with-answers',
                stdout=stdout,
            )

        request = use_case.request
        self.assertEqual(request.work_id, 'work-1')
        self.assertEqual(request.options.renderer_type, 'pdf')
        self.assertEqual(request.options.pdf_format, 'A5')
        self.assertEqual(request.options.answer_type, 'with_answers')
        self.assertIn('Created PDF document for Контрольная', stdout.getvalue())
        self.assertIn('work_1.pdf', stdout.getvalue())

    def test_command_raises_for_missing_work(self):
        use_case = FakeRenderWorkDocumentUseCase(
            result=DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type='pdf',
            ),
        )

        with patch(
            'pdf_generator.management.commands.generate_pdf.container',
            FakeDocumentRenderContainer(use_case),
        ):
            with self.assertRaises(CommandError):
                call_command('generate_pdf', 'work', 'missing')


class FakeDocumentRenderContainer:
    def __init__(self, use_case):
        self.use_case = use_case

    def render_work_document_use_case(self):
        return self.use_case


class FakeRenderWorkDocumentUseCase:
    def __init__(self, result):
        self.result = result
        self.request = None

    def execute(self, request):
        self.request = request
        return self.result
