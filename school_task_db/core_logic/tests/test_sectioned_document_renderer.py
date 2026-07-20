from unittest import TestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.services.sectioned_document_renderer import (
    SectionedDocumentContentRenderer,
    WrappedDocumentContentRenderer,
)
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_plan import DocumentRenderRequest


class SectionedDocumentContentRendererTests(TestCase):
    def test_renders_document_sections_in_order(self):
        registry = FakeSectionRendererRegistry()
        renderer = SectionedDocumentContentRenderer(
            section_renderer_registry=registry,
        )
        document = Document(
            title='Контрольная',
            sections=[
                DocumentSection(section_type='header'),
                DocumentSection(section_type='task_list'),
                DocumentSection(section_type='answers'),
            ],
        )
        request = DocumentRenderRequest(
            document=document,
            render_target=RenderTarget(renderer_type='html'),
        )

        content = renderer.render_content(request)

        self.assertEqual(
            content,
            '<html:header>\n<html:task_list>\n<html:answers>',
        )
        self.assertEqual(
            [
                section_request.section.section_type
                for section_request in registry.requests
            ],
            ['header', 'task_list', 'answers'],
        )
        self.assertTrue(
            all(
                section_request.document is document
                for section_request in registry.requests
            )
        )

    def test_uses_configured_section_separator(self):
        registry = FakeSectionRendererRegistry()
        renderer = SectionedDocumentContentRenderer(
            section_renderer_registry=registry,
            section_separator='\n\n',
        )
        request = DocumentRenderRequest(
            document=Document(
                title='Контрольная',
                sections=[
                    DocumentSection(section_type='header'),
                    DocumentSection(section_type='task_list'),
                ],
            ),
            render_target=RenderTarget(renderer_type='latex'),
        )

        content = renderer.render_content(request)

        self.assertEqual(content, '<latex:header>\n\n<latex:task_list>')


class WrappedDocumentContentRendererTests(TestCase):
    def test_wraps_rendered_body_content(self):
        body_renderer = FakeBodyRenderer(body_content='<section>body</section>')
        document_wrapper = FakeDocumentWrapper()
        renderer = WrappedDocumentContentRenderer(
            body_renderer=body_renderer,
            document_wrapper=document_wrapper,
        )
        request = DocumentRenderRequest(
            document=Document(title='Контрольная'),
            render_target=RenderTarget(renderer_type='html'),
        )

        content = renderer.render_content(request)

        self.assertEqual(content, '<html><section>body</section></html>')
        self.assertEqual(body_renderer.request, request)
        self.assertEqual(document_wrapper.request.document, request.document)
        self.assertEqual(document_wrapper.request.render_target, request.render_target)
        self.assertEqual(
            document_wrapper.request.body_content,
            '<section>body</section>',
        )


class FakeSectionRendererRegistry:
    def __init__(self):
        self.requests = []

    def render_section(self, request):
        self.requests.append(request)
        return (
            f'<{request.render_target.renderer_type}:'
            f'{request.section.section_type}>'
        )


class FakeBodyRenderer:
    def __init__(self, body_content):
        self.body_content = body_content
        self.request = None

    def render_content(self, request):
        self.request = request
        return self.body_content


class FakeDocumentWrapper:
    def __init__(self):
        self.request = None

    def wrap_content(self, request):
        self.request = request
        return f'<html>{request.body_content}</html>'
