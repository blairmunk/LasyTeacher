"""Template-backed document section renderer."""

from django.template.loader import render_to_string

from core_logic.interfaces.document_rendering import IDocumentSectionRenderer
from core_logic.value_objects.document_render_plan import (
    DocumentSectionRenderRequest,
)


class TemplateDocumentSectionRenderer(IDocumentSectionRenderer):
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

    def render_section(self, request: DocumentSectionRenderRequest) -> str:
        return self.template_renderer(
            self.template_name,
            self._template_context(request),
        )

    def _template_context(self, request: DocumentSectionRenderRequest) -> dict:
        return {
            **self.extra_context,
            'document': request.document,
            'section': request.section,
            'payload': dict(request.section.payload),
            'render_target': request.render_target,
        }
