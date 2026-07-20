"""Compose document content from section renderers."""

from core_logic.value_objects.document_render_plan import (
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
