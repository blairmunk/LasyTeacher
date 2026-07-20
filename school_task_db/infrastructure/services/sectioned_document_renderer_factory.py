"""Factories for section-based text document renderers."""

from dataclasses import dataclass
from typing import Callable, Mapping

from core_logic.services.document_renderer_registry import DocumentRendererRegistry
from core_logic.services.sectioned_document_renderer import (
    SectionedDocumentContentRenderer,
    WrappedDocumentContentRenderer,
)
from core_logic.value_objects.document_render_plan import DocumentRenderRequest
from infrastructure.services.sectioned_document_file_renderer import (
    SectionedHtmlToPdfDocumentRenderer,
    SectionedDocumentFileRenderer,
)
from infrastructure.services.template_section_renderer_registry_factory import (
    build_template_section_renderer_registry,
)
from infrastructure.services.template_document_content_wrapper import (
    TemplateDocumentContentWrapper,
)


@dataclass(frozen=True)
class TemplateSectionedTextDocumentRendererSpec:
    document_type: str
    section_templates: Mapping[str, str]
    filename_builder: Callable[[DocumentRenderRequest], str]
    wrapper_template_name: str = ''
    section_separator: str = '\n'

    def __post_init__(self):
        if not self.document_type:
            raise ValueError('document_type is required')


def build_sectioned_text_document_renderer(
    renderer_type: str,
    section_renderer_registry,
    filename_builder,
    file_store,
    section_separator='\n',
    document_wrapper=None,
) -> SectionedDocumentFileRenderer:
    if not renderer_type:
        raise ValueError('renderer_type is required')

    body_renderer = SectionedDocumentContentRenderer(
        section_renderer_registry=section_renderer_registry,
        section_separator=section_separator,
    )
    content_renderer = (
        WrappedDocumentContentRenderer(
            body_renderer=body_renderer,
            document_wrapper=document_wrapper,
        )
        if document_wrapper
        else body_renderer
    )

    return SectionedDocumentFileRenderer(
        file_type=renderer_type,
        filename_builder=filename_builder,
        content_renderer=content_renderer,
        file_store=file_store,
    )


def build_sectioned_html_to_pdf_document_renderer(
    section_renderer_registry,
    html_filename_builder,
    file_store,
    section_separator='\n',
    document_wrapper=None,
    html_to_pdf_renderer_factory=None,
) -> SectionedHtmlToPdfDocumentRenderer:
    body_renderer = SectionedDocumentContentRenderer(
        section_renderer_registry=section_renderer_registry,
        section_separator=section_separator,
    )
    content_renderer = (
        WrappedDocumentContentRenderer(
            body_renderer=body_renderer,
            document_wrapper=document_wrapper,
        )
        if document_wrapper
        else body_renderer
    )

    return SectionedHtmlToPdfDocumentRenderer(
        html_filename_builder=html_filename_builder,
        html_content_renderer=content_renderer,
        file_store=file_store,
        html_to_pdf_renderer_factory=html_to_pdf_renderer_factory,
    )


def build_template_sectioned_text_document_renderer(
    renderer_type: str,
    section_templates,
    filename_builder,
    file_store,
    template_renderer=None,
    section_separator='\n',
    wrapper_template_name='',
) -> SectionedDocumentFileRenderer:
    section_renderer_registry = build_template_section_renderer_registry(
        renderer_type=renderer_type,
        section_templates=section_templates,
        template_renderer=template_renderer,
    )
    document_wrapper = (
        TemplateDocumentContentWrapper(
            template_name=wrapper_template_name,
            template_renderer=template_renderer,
        )
        if wrapper_template_name
        else None
    )
    return build_sectioned_text_document_renderer(
        renderer_type=renderer_type,
        section_renderer_registry=section_renderer_registry,
        filename_builder=filename_builder,
        file_store=file_store,
        section_separator=section_separator,
        document_wrapper=document_wrapper,
    )


def build_template_sectioned_text_document_renderer_registry(
    renderer_type: str,
    renderer_specs,
    file_store,
    template_renderer=None,
) -> DocumentRendererRegistry:
    if not renderer_type:
        raise ValueError('renderer_type is required')

    registry = DocumentRendererRegistry()
    for spec in renderer_specs:
        renderer = build_template_sectioned_text_document_renderer(
            renderer_type=renderer_type,
            section_templates=spec.section_templates,
            filename_builder=spec.filename_builder,
            file_store=file_store,
            template_renderer=template_renderer,
            section_separator=spec.section_separator,
            wrapper_template_name=spec.wrapper_template_name,
        )
        registry.register(
            renderer_type,
            renderer,
            document_type=spec.document_type,
        )
    return registry


def build_template_sectioned_html_to_pdf_document_renderer_registry(
    renderer_type: str,
    renderer_specs,
    file_store,
    template_renderer=None,
    html_to_pdf_renderer_factory=None,
) -> DocumentRendererRegistry:
    if not renderer_type:
        raise ValueError('renderer_type is required')

    registry = DocumentRendererRegistry()
    for spec in renderer_specs:
        section_renderer_registry = build_template_section_renderer_registry(
            renderer_type='html',
            section_templates=spec.section_templates,
            template_renderer=template_renderer,
        )
        document_wrapper = (
            TemplateDocumentContentWrapper(
                template_name=spec.wrapper_template_name,
                template_renderer=template_renderer,
            )
            if spec.wrapper_template_name
            else None
        )
        renderer = build_sectioned_html_to_pdf_document_renderer(
            section_renderer_registry=section_renderer_registry,
            html_filename_builder=spec.filename_builder,
            file_store=file_store,
            section_separator=spec.section_separator,
            document_wrapper=document_wrapper,
            html_to_pdf_renderer_factory=html_to_pdf_renderer_factory,
        )
        registry.register(
            renderer_type,
            renderer,
            document_type=spec.document_type,
        )
    return registry
