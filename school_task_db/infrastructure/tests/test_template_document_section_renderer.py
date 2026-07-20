from unittest import TestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_requests import (
    DocumentSectionRenderRequest,
)
from infrastructure.services.template_document_section_renderer import (
    TemplateDocumentSectionRenderer,
)


class TemplateDocumentSectionRendererTests(TestCase):
    def test_renders_section_with_template_context(self):
        template_calls = []

        def template_renderer(template_name, context):
            template_calls.append((template_name, context))
            return '<section>rendered</section>'

        renderer = TemplateDocumentSectionRenderer(
            template_name='documents/sections/task_list.html',
            template_renderer=template_renderer,
        )
        document = Document(title='Контрольная')
        section = DocumentSection(
            section_type='task_list',
            title='Задания',
            payload={'include_hints': True},
        )
        render_target = RenderTarget(renderer_type='html')

        result = renderer.render_section(
            DocumentSectionRenderRequest(
                document=document,
                section=section,
                render_target=render_target,
            )
        )

        template_name, context = template_calls[0]
        self.assertEqual(result, '<section>rendered</section>')
        self.assertEqual(template_name, 'documents/sections/task_list.html')
        self.assertEqual(context['document'], document)
        self.assertEqual(context['section'], section)
        self.assertEqual(context['payload'], {'include_hints': True})
        self.assertEqual(context['render_target'], render_target)

    def test_includes_extra_context(self):
        def template_renderer(template_name, context):
            return context['theme']

        renderer = TemplateDocumentSectionRenderer(
            template_name='documents/sections/header.html',
            template_renderer=template_renderer,
            extra_context={'theme': 'print'},
        )

        result = renderer.render_section(
            DocumentSectionRenderRequest(
                document=Document(title='Контрольная'),
                section=DocumentSection(section_type='header'),
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertEqual(result, 'print')

    def test_rejects_empty_template_name(self):
        with self.assertRaises(ValueError):
            TemplateDocumentSectionRenderer(template_name='')
