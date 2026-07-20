from unittest import TestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_plan import (
    DocumentSectionRenderRequest,
)
from infrastructure.services.template_section_renderer_registry_factory import (
    build_template_section_renderer_registry,
)


class TemplateSectionRendererRegistryFactoryTests(TestCase):
    def test_builds_template_backed_section_registry(self):
        template_calls = []

        def template_renderer(template_name, context):
            template_calls.append((template_name, context))
            return f'<rendered>{template_name}</rendered>'

        registry = build_template_section_renderer_registry(
            renderer_type='html',
            section_templates={
                'header': 'documents/html/header.html',
                'task_list': 'documents/html/task_list.html',
            },
            template_renderer=template_renderer,
        )
        document = Document(title='Контрольная')
        section = DocumentSection(
            section_type='task_list',
            payload={'include_hints': True},
        )

        result = registry.render_section(
            DocumentSectionRenderRequest(
                document=document,
                section=section,
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        template_name, context = template_calls[0]
        self.assertEqual(result, '<rendered>documents/html/task_list.html</rendered>')
        self.assertEqual(template_name, 'documents/html/task_list.html')
        self.assertEqual(context['document'], document)
        self.assertEqual(context['section'], section)

    def test_rejects_empty_renderer_type(self):
        with self.assertRaises(ValueError):
            build_template_section_renderer_registry(
                renderer_type='',
                section_templates={},
            )
