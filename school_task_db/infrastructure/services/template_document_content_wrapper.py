"""Template-backed wrapper for rendered document section body."""

from django.template.loader import render_to_string

from core_logic.interfaces.document_rendering import IDocumentContentWrapper
from core_logic.value_objects.document_render_plan import (
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
        context = {
            'document': request.document,
            'render_target': request.render_target,
            'body_content': request.body_content,
            **self.extra_context,
        }
        return self.template_renderer(self.template_name, context)
