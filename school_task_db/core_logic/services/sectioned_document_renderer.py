"""Compose document content from section renderers."""

from core_logic.value_objects.document_render_plan import (
    DocumentContentWrapRequest,
    DocumentRenderRequest,
    DocumentSectionRenderRequest,
)


class SectionedDocumentContentRenderer:
    def __init__(self, section_renderer_registry, section_separator='\n'):
        self.section_renderer_registry = section_renderer_registry
        self.section_separator = section_separator

    def render_content(self, request: DocumentRenderRequest) -> str:
        rendered_sections = [
            self.section_renderer_registry.render_section(
                DocumentSectionRenderRequest(
                    document=request.document,
                    section=section,
                    render_target=request.render_target,
                )
            )
            for section in request.document.sections
        ]
        return self.section_separator.join(rendered_sections)


class WrappedDocumentContentRenderer:
    def __init__(self, body_renderer, document_wrapper):
        self.body_renderer = body_renderer
        self.document_wrapper = document_wrapper

    def render_content(self, request: DocumentRenderRequest) -> str:
        body_content = self.body_renderer.render_content(request)
        return self.document_wrapper.wrap_content(
            DocumentContentWrapRequest(
                document=request.document,
                render_target=request.render_target,
                body_content=body_content,
            )
        )
