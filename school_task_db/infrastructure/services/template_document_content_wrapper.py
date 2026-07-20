"""Template-backed wrapper for rendered document section body."""

from django.template.loader import render_to_string
from django.template import Context, Engine
from django.utils.safestring import mark_safe

from core_logic.interfaces.document_rendering import IDocumentContentWrapper
from core_logic.value_objects.document_render_requests import (
    DocumentContentWrapRequest,
)


class TemplateDocumentContentWrapper(IDocumentContentWrapper):
    def __init__(
        self,
        template_name: str,
        template_renderer=render_to_string,
        extra_context=None,
    ):
        if not template_name:
            raise ValueError('template_name is required')

        self.template_name = template_name
        self.template_renderer = template_renderer or render_to_string
        self.extra_context = extra_context or {}

    def wrap_content(self, request: DocumentContentWrapRequest) -> str:
        presentation = request.document.presentation
        context = {
            'document': request.document,
            'render_target': request.render_target,
            'body_content': mark_safe(request.body_content),
            'presentation': presentation,
            'custom_css': presentation.custom_css,
            'custom_latex_preamble': presentation.custom_latex_preamble,
            **self.extra_context,
        }
        template_override = presentation.template_override_for_renderer(
            request.render_target.renderer_type,
        )
        if template_override:
            return Engine.get_default().from_string(template_override).render(
                Context(context),
            )
        return self.template_renderer(self.template_name, context)
