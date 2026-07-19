from unittest import TestCase

from core_logic.entities.document import Document
from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.services.document_renderer_registry import (
    DocumentRendererRegistry,
    UnsupportedDocumentRenderer,
)
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_render_plan import DocumentRenderRequest


class FakeRenderer:
    def __init__(self):
        self.request = None

    def render(self, request):
        self.request = request
        return GeneratedDocument(file_type=request.render_target.renderer_type)


class DocumentRendererRegistryTests(TestCase):
    def test_registers_and_delegates_to_renderer(self):
        registry = DocumentRendererRegistry()
        renderer = FakeRenderer()
        registry.register('html', renderer, document_type='work')
        request = DocumentRenderRequest(
            document=Document(title='Контрольная', document_type='work'),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = registry.render(request)

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(renderer.request, request)

    def test_rejects_empty_renderer_type(self):
        registry = DocumentRendererRegistry()

        with self.assertRaises(ValueError):
            registry.register('', FakeRenderer())

    def test_can_register_same_renderer_type_for_different_documents(self):
        registry = DocumentRendererRegistry()
        work_renderer = FakeRenderer()
        remedial_renderer = FakeRenderer()
        registry.register('html', work_renderer, document_type='work')
        registry.register(
            'html',
            remedial_renderer,
            document_type='remedial_sheet',
        )
        work_request = DocumentRenderRequest(
            document=Document(title='Контрольная', document_type='work'),
            render_target=RenderTarget(renderer_type='html'),
        )
        remedial_request = DocumentRenderRequest(
            document=Document(title='Разбор', document_type='remedial_sheet'),
            render_target=RenderTarget(renderer_type='html'),
        )

        registry.render(work_request)
        registry.render(remedial_request)

        self.assertEqual(work_renderer.request, work_request)
        self.assertEqual(remedial_renderer.request, remedial_request)

    def test_rejects_unsupported_renderer_type(self):
        registry = DocumentRendererRegistry()
        request = DocumentRenderRequest(
            document=Document(title='Контрольная', document_type='work'),
            render_target=RenderTarget(renderer_type='pdf'),
        )

        with self.assertRaises(UnsupportedDocumentRenderer):
            registry.render(request)
