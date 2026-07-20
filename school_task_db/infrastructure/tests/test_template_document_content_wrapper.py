from unittest import TestCase

from core_logic.entities.document import Document, DocumentPresentation
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_requests import (
    DocumentContentWrapRequest,
)
from infrastructure.services.template_document_content_wrapper import (
    TemplateDocumentContentWrapper,
)


class TemplateDocumentContentWrapperTests(TestCase):
    def test_wraps_content_with_template_context(self):
        template_calls = []

        def template_renderer(template_name, context):
            template_calls.append((template_name, context))
            return f"<html>{context['body_content']}</html>"

        wrapper = TemplateDocumentContentWrapper(
            template_name='documents/html/base/document.html',
            template_renderer=template_renderer,
        )
        document = Document(title='Контрольная')
        render_target = RenderTarget(renderer_type='html')

        result = wrapper.wrap_content(
            DocumentContentWrapRequest(
                document=document,
                render_target=render_target,
                body_content='<section>body</section>',
            )
        )

        template_name, context = template_calls[0]
        self.assertEqual(result, '<html><section>body</section></html>')
        self.assertEqual(template_name, 'documents/html/base/document.html')
        self.assertEqual(context['document'], document)
        self.assertEqual(context['render_target'], render_target)
        self.assertEqual(context['body_content'], '<section>body</section>')

    def test_includes_extra_context(self):
        def template_renderer(template_name, context):
            return context['theme']

        wrapper = TemplateDocumentContentWrapper(
            template_name='documents/html/base/document.html',
            template_renderer=template_renderer,
            extra_context={'theme': 'print'},
        )

        result = wrapper.wrap_content(
            DocumentContentWrapRequest(
                document=Document(title='Контрольная'),
                render_target=RenderTarget(renderer_type='html'),
                body_content='body',
            )
        )

        self.assertEqual(result, 'print')

    def test_renders_wrapper_template_override_from_document_presentation(self):
        wrapper = TemplateDocumentContentWrapper(
            template_name='documents/html/base/document.html',
            template_renderer=lambda template_name, context: 'default',
        )
        document = Document(
            title='Контрольная',
            presentation=DocumentPresentation(
                html_template_override=(
                    '<article>{{ document.title }}: {{ body_content }}</article>'
                ),
            ),
        )

        result = wrapper.wrap_content(
            DocumentContentWrapRequest(
                document=document,
                render_target=RenderTarget(renderer_type='html'),
                body_content='<section>body</section>',
            )
        )

        self.assertEqual(
            result,
            '<article>Контрольная: <section>body</section></article>',
        )

    def test_exposes_custom_css_and_latex_preamble_to_templates(self):
        def template_renderer(template_name, context):
            return (
                f"{context['custom_css']}|"
                f"{context['custom_latex_preamble']}"
            )

        wrapper = TemplateDocumentContentWrapper(
            template_name='documents/html/base/document.html',
            template_renderer=template_renderer,
        )
        document = Document(
            title='Контрольная',
            presentation=DocumentPresentation(
                custom_css='body { color: black; }',
                custom_latex_preamble='\\usepackage{multicol}',
            ),
        )

        result = wrapper.wrap_content(
            DocumentContentWrapRequest(
                document=document,
                render_target=RenderTarget(renderer_type='html'),
                body_content='body',
            )
        )

        self.assertEqual(result, 'body { color: black; }|\\usepackage{multicol}')

    def test_uses_default_template_renderer_when_none_passed(self):
        wrapper = TemplateDocumentContentWrapper(
            template_name='documents/html/base/document.html',
            template_renderer=None,
        )

        result = wrapper.wrap_content(
            DocumentContentWrapRequest(
                document=Document(title='Контрольная'),
                render_target=RenderTarget(renderer_type='html'),
                body_content='<section>body</section>',
            )
        )

        self.assertIn('<title>Контрольная</title>', result)
        self.assertIn('<section>body</section>', result)

    def test_rejects_empty_template_name(self):
        with self.assertRaises(ValueError):
            TemplateDocumentContentWrapper(template_name='')
