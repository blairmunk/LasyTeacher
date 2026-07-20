"""Factories for template-backed document section renderer registries."""

from core_logic.services.document_renderer_registry import (
    DocumentSectionRendererRegistry,
)
from infrastructure.services.template_document_section_renderer import (
    TemplateDocumentSectionRenderer,
)


def build_template_section_renderer_registry(
    renderer_type: str,
    section_templates,
    template_renderer=None,
) -> DocumentSectionRendererRegistry:
    if not renderer_type:
        raise ValueError('renderer_type is required')

    registry = DocumentSectionRendererRegistry()
    for section_type, template_name in section_templates.items():
        registry.register(
            renderer_type=renderer_type,
            section_type=section_type,
            renderer=TemplateDocumentSectionRenderer(
                template_name=template_name,
                template_renderer=template_renderer,
            ),
        )
    return registry
