from django.test import SimpleTestCase

from core_logic.entities.document import Document
from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_render_plan import DocumentRenderRequest
from infrastructure.services.sectioned_document_file_renderer import (
    SectionedDocumentFileRenderer,
)


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


class FakeContentRenderer:
    def __init__(self, content='content'):
        self.content = content
        self.request = None

    def render_content(self, request):
        self.request = request
        return self.content


class FakeFileStore:
    def __init__(self):
        self.request = None

    def write_text_document(self, file_type, filename, content):
        self.request = (file_type, filename, content)
        return GeneratedDocument(file_type=file_type)
