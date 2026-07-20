from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from core_logic.entities.document import Document
from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_render_plan import DocumentRenderRequest
from infrastructure.services.sectioned_document_file_renderer import (
    SectionedHtmlToPdfDocumentRenderer,
    SectionedDocumentFileRenderer,
)
from infrastructure.services.html_to_pdf_renderer import HtmlToPdfRenderer


class SectionedDocumentFileRendererTests(SimpleTestCase):
    def test_renders_sectioned_content_to_text_document(self):
        content_renderer = FakeContentRenderer(content='<html>work</html>')
        file_store = FakeFileStore()
        renderer = SectionedDocumentFileRenderer(
            file_type='html',
            filename_builder=lambda request: f'{request.document.title}.html',
            content_renderer=content_renderer,
            file_store=file_store,
        )
        request = DocumentRenderRequest(
            document=Document(title='work-1'),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = renderer.render(request)

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(content_renderer.request, request)
        self.assertEqual(
            file_store.request,
            ('html', 'work-1.html', '<html>work</html>'),
        )

    def test_rejects_empty_file_type(self):
        with self.assertRaises(ValueError):
            SectionedDocumentFileRenderer(
                file_type='',
                filename_builder=lambda request: 'work.html',
                content_renderer=FakeContentRenderer(),
                file_store=FakeFileStore(),
            )

    def test_rejects_empty_filename(self):
        renderer = SectionedDocumentFileRenderer(
            file_type='html',
            filename_builder=lambda request: '',
            content_renderer=FakeContentRenderer(),
            file_store=FakeFileStore(),
        )

        with self.assertRaises(ValueError):
            renderer.render(
                DocumentRenderRequest(
                    document=Document(title='work'),
                    render_target=RenderTarget(renderer_type='html'),
                )
            )


class SectionedHtmlToPdfDocumentRendererTests(SimpleTestCase):
    def test_renders_sectioned_html_to_pdf_document(self):
        content_renderer = FakeContentRenderer(content='<html>work</html>')
        with TemporaryDirectory() as output_dir:
            file_store = FakeFileStore(output_dirs={'pdf': output_dir})
            html_to_pdf_renderer = FakeHtmlToPdfRenderer()
            renderer = SectionedHtmlToPdfDocumentRenderer(
                html_filename_builder=lambda request: (
                    f'{request.document.title}.html'
                ),
                html_content_renderer=content_renderer,
                file_store=file_store,
                html_to_pdf_renderer_factory=(
                    lambda request: html_to_pdf_renderer
                ),
            )
            request = DocumentRenderRequest(
                document=Document(title='work-1'),
                render_target=RenderTarget(
                    renderer_type='pdf',
                    page_format='A5',
                ),
            )

            result = renderer.render(request)

            html_path, pdf_path = html_to_pdf_renderer.request
            self.assertEqual(result.file_type, 'pdf')
            self.assertEqual(
                content_renderer.request.render_target.renderer_type,
                'html',
            )
            self.assertEqual(
                content_renderer.request.render_target.page_format,
                'A5',
            )
            self.assertEqual(html_path.name, 'work-1.html')
            self.assertEqual(
                html_to_pdf_renderer.html_content,
                '<html>work</html>',
            )
            self.assertEqual(pdf_path, Path(output_dir) / 'work-1.pdf')
            self.assertEqual(file_store.path_requests, [('pdf', [pdf_path])])

    def test_rejects_missing_pdf_output_dir(self):
        renderer = SectionedHtmlToPdfDocumentRenderer(
            html_filename_builder=lambda request: 'work.html',
            html_content_renderer=FakeContentRenderer(),
            file_store=FakeFileStore(output_dirs={}),
            html_to_pdf_renderer_factory=lambda request: FakeHtmlToPdfRenderer(),
        )

        with self.assertRaises(ValueError):
            renderer.render(
                DocumentRenderRequest(
                    document=Document(title='work'),
                    render_target=RenderTarget(renderer_type='pdf'),
                )
            )

    def test_default_html_to_pdf_renderer_uses_infrastructure_backend(self):
        renderer = SectionedHtmlToPdfDocumentRenderer(
            html_filename_builder=lambda request: 'work.html',
            html_content_renderer=FakeContentRenderer(),
            file_store=FakeFileStore(),
        )
        request = DocumentRenderRequest(
            document=Document(title='work'),
            render_target=RenderTarget(renderer_type='pdf', page_format='A5'),
        )

        html_to_pdf_renderer = renderer._default_html_to_pdf_renderer(request)

        self.assertIsInstance(html_to_pdf_renderer, HtmlToPdfRenderer)
        self.assertEqual(html_to_pdf_renderer.options['format'], 'A5')


class FakeContentRenderer:
    def __init__(self, content='content'):
        self.content = content
        self.request = None

    def render_content(self, request):
        self.request = request
        return self.content


class FakeFileStore:
    def __init__(self, output_dirs=None):
        self.request = None
        self.path_requests = []
        self.output_dirs = output_dirs or {}

    def write_text_document(self, file_type, filename, content):
        self.request = (file_type, filename, content)
        return GeneratedDocument(file_type=file_type)

    def document_from_paths(self, file_type, file_paths):
        self.path_requests.append((file_type, file_paths))
        return GeneratedDocument(file_type=file_type)


class FakeHtmlToPdfRenderer:
    def __init__(self):
        self.request = None
        self.html_content = ''

    def generate_pdf(self, html_path, pdf_path):
        self.request = (html_path, pdf_path)
        self.html_content = html_path.read_text(encoding='utf-8')
        pdf_path.write_bytes(b'pdf')
        return pdf_path
