"""Factories for section-based text document renderers."""

from core_logic.services.sectioned_document_renderer import (
    SectionedDocumentContentRenderer,
)
from infrastructure.services.sectioned_document_file_renderer import (
    SectionedDocumentFileRenderer,
)
from infrastructure.services.template_section_renderer_registry_factory import (
    build_template_section_renderer_registry,
)


def build_sectioned_text_document_renderer(
    renderer_type: str,
    section_renderer_registry,
    filename_builder,
    file_store,
    section_separator='\n',
) -> SectionedDocumentFileRenderer:
    if not renderer_type:
        raise ValueError('renderer_type is required')

    return SectionedDocumentFileRenderer(
        file_type=renderer_type,
        filename_builder=filename_builder,
        content_renderer=SectionedDocumentContentRenderer(
            section_renderer_registry=section_renderer_registry,
            section_separator=section_separator,
        ),
        file_store=file_store,
    )


def build_template_sectioned_text_document_renderer(
    renderer_type: str,
    section_templates,
    filename_builder,
    file_store,
    template_renderer=None,
    section_separator='\n',
) -> SectionedDocumentFileRenderer:
    section_renderer_registry = build_template_section_renderer_registry(
        renderer_type=renderer_type,
        section_templates=section_templates,
        template_renderer=template_renderer,
    )
    return build_sectioned_text_document_renderer(
        renderer_type=renderer_type,
        section_renderer_registry=section_renderer_registry,
        filename_builder=filename_builder,
        file_store=file_store,
        section_separator=section_separator,
    )
