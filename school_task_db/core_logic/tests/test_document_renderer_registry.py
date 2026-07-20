from unittest import TestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.services.document_renderer_registry import (
    DocumentRendererRegistry,
    DocumentSectionRendererRegistry,
    UnsupportedDocumentRenderer,
)
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_plan import (
    DocumentRenderRequest,
    DocumentSectionRenderRequest,
)


class FakeRenderer:
    def __init__(self):
        self.request = None

    def render(self, request):
        self.request = request
        return GeneratedDocument(file_type=request.render_target.renderer_type)


class FakeSectionRenderer:
    def __init__(self):
        self.request = None

    def render_section(self, request):
        self.request = request
        return f'{request.render_target.renderer_type}:{request.section.section_type}'


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

    def test_extends_from_another_renderer_registry(self):
        registry = DocumentRendererRegistry()
        other_registry = DocumentRendererRegistry()
        renderer = FakeRenderer()
        other_registry.register('html', renderer, document_type='work')
        request = DocumentRenderRequest(
            document=Document(title='Контрольная', document_type='work'),
            render_target=RenderTarget(renderer_type='html'),
        )

        registry.extend(other_registry)
        result = registry.render(request)

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(renderer.request, request)


class DocumentSectionRendererRegistryTests(TestCase):
    def test_registers_and_delegates_to_section_renderer(self):
        registry = DocumentSectionRendererRegistry()
        renderer = FakeSectionRenderer()
        registry.register('html', 'task_list', renderer)
        request = DocumentSectionRenderRequest(
            document=Document(title='Контрольная'),
            section=DocumentSection(section_type='task_list'),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = registry.render_section(request)

        self.assertEqual(result, 'html:task_list')
        self.assertEqual(renderer.request, request)

    def test_can_register_same_section_for_different_renderers(self):
        registry = DocumentSectionRendererRegistry()
        html_renderer = FakeSectionRenderer()
        latex_renderer = FakeSectionRenderer()
        registry.register('html', 'task_list', html_renderer)
        registry.register('latex', 'task_list', latex_renderer)
        document = Document(title='Контрольная')
        section = DocumentSection(section_type='task_list')
        html_request = DocumentSectionRenderRequest(
            document=document,
            section=section,
            render_target=RenderTarget(renderer_type='html'),
        )
        latex_request = DocumentSectionRenderRequest(
            document=document,
            section=section,
            render_target=RenderTarget(renderer_type='latex'),
        )

        registry.render_section(html_request)
        registry.render_section(latex_request)

        self.assertEqual(html_renderer.request, html_request)
        self.assertEqual(latex_renderer.request, latex_request)

    def test_rejects_empty_section_renderer_keys(self):
        registry = DocumentSectionRendererRegistry()

        with self.assertRaises(ValueError):
            registry.register('', 'task_list', FakeSectionRenderer())
        with self.assertRaises(ValueError):
            registry.register('html', '', FakeSectionRenderer())

    def test_rejects_unsupported_section_renderer(self):
        registry = DocumentSectionRendererRegistry()
        request = DocumentSectionRenderRequest(
            document=Document(title='Контрольная'),
            section=DocumentSection(section_type='task_list'),
            render_target=RenderTarget(renderer_type='html'),
        )

        with self.assertRaises(UnsupportedDocumentRenderer):
            registry.render_section(request)

    def test_extends_from_another_section_renderer_registry(self):
        registry = DocumentSectionRendererRegistry()
        other_registry = DocumentSectionRendererRegistry()
        renderer = FakeSectionRenderer()
        other_registry.register('html', 'task_list', renderer)
        request = DocumentSectionRenderRequest(
            document=Document(title='Контрольная'),
            section=DocumentSection(section_type='task_list'),
            render_target=RenderTarget(renderer_type='html'),
        )

        registry.extend(other_registry)
        result = registry.render_section(request)

        self.assertEqual(result, 'html:task_list')
        self.assertEqual(renderer.request, request)
