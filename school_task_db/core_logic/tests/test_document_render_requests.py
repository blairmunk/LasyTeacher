from unittest import TestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_requests import (
    DocumentContentWrapRequest,
    DocumentRenderRequest,
    DocumentSectionRenderRequest,
)


class DocumentRenderRequestTests(TestCase):
    def test_render_request_groups_document_and_target(self):
        document = Document(title='Контрольная')
        render_target = RenderTarget(renderer_type='pdf')

        request = DocumentRenderRequest(
            document=document,
            render_target=render_target,
        )

        self.assertEqual(request.document.title, 'Контрольная')
        self.assertEqual(request.render_target.renderer_type, 'pdf')

    def test_section_render_request_groups_document_section_and_target(self):
        document = Document(title='Контрольная')
        section = DocumentSection(section_type='task_list')
        render_target = RenderTarget(renderer_type='html')

        request = DocumentSectionRenderRequest(
            document=document,
            section=section,
            render_target=render_target,
        )

        self.assertEqual(request.document.title, 'Контрольная')
        self.assertEqual(request.section.section_type, 'task_list')
        self.assertEqual(request.render_target.renderer_type, 'html')

    def test_content_wrap_request_groups_document_target_and_body(self):
        document = Document(title='Контрольная')
        render_target = RenderTarget(renderer_type='html')

        request = DocumentContentWrapRequest(
            document=document,
            render_target=render_target,
            body_content='<section>body</section>',
        )

        self.assertEqual(request.document.title, 'Контрольная')
        self.assertEqual(request.render_target.renderer_type, 'html')
        self.assertEqual(request.body_content, '<section>body</section>')
