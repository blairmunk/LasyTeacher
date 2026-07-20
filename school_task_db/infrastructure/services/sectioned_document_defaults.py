"""Default component wiring for section-based document rendering."""

from dataclasses import dataclass

from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.services.document_renderer_registry import DocumentRendererRegistry
from infrastructure.services.django_document_section_payloads import (
    build_remedial_sheet_section_payload_builder_registry,
    build_work_section_payload_builder_registry,
)
from infrastructure.services.latex_document_payloads import (
    LatexTaskPayloadFormatter,
    RenderTargetTaskPayloadFormatter,
)
from infrastructure.services.sectioned_document_renderer_factory import (
    build_template_sectioned_html_to_pdf_document_renderer_registry,
    build_template_sectioned_text_document_renderer_registry,
)
from infrastructure.services.sectioned_document_renderer_specs import (
    remedial_html_renderer_specs,
    remedial_latex_renderer_specs,
    sectioned_html_renderer_specs,
    sectioned_latex_renderer_specs,
    work_html_renderer_specs,
    work_latex_renderer_specs,
)


@dataclass(frozen=True)
class SectionedDocumentComponents:
    document_builder: RecipeDocumentBuilder
    document_renderer_registry: DocumentRendererRegistry


def build_sectioned_work_html_document_components(
    file_store,
    get_work_source=None,
    template_renderer=None,
) -> SectionedDocumentComponents:
    payload_registry = build_work_section_payload_builder_registry(
        get_work_source=get_work_source,
    )
    return SectionedDocumentComponents(
        document_builder=RecipeDocumentBuilder(
            section_payload_builder_registry=payload_registry,
        ),
        document_renderer_registry=(
            build_template_sectioned_text_document_renderer_registry(
                renderer_type='html',
                renderer_specs=work_html_renderer_specs(),
                file_store=file_store,
                template_renderer=template_renderer,
            )
        ),
    )


def build_sectioned_work_latex_document_components(
    file_store,
    get_work_source=None,
    template_renderer=None,
    task_payload_formatter=None,
) -> SectionedDocumentComponents:
    payload_registry = build_work_section_payload_builder_registry(
        get_work_source=get_work_source,
        task_payload_formatter=(
            task_payload_formatter or LatexTaskPayloadFormatter()
        ),
    )
    return SectionedDocumentComponents(
        document_builder=RecipeDocumentBuilder(
            section_payload_builder_registry=payload_registry,
        ),
        document_renderer_registry=(
            build_template_sectioned_text_document_renderer_registry(
                renderer_type='latex',
                renderer_specs=work_latex_renderer_specs(),
                file_store=file_store,
                template_renderer=template_renderer,
            )
        ),
    )


def build_sectioned_html_document_components(
    file_store,
    get_work_source=None,
    get_remedial_sheet_data=None,
    template_renderer=None,
    task_payload_formatter=None,
) -> SectionedDocumentComponents:
    payload_registry = build_work_section_payload_builder_registry(
        get_work_source=get_work_source,
        task_payload_formatter=task_payload_formatter,
    )
    payload_registry.extend(
        build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=get_remedial_sheet_data,
            task_payload_formatter=task_payload_formatter,
        )
    )
    return SectionedDocumentComponents(
        document_builder=RecipeDocumentBuilder(
            section_payload_builder_registry=payload_registry,
        ),
        document_renderer_registry=(
            build_template_sectioned_text_document_renderer_registry(
                renderer_type='html',
                renderer_specs=sectioned_html_renderer_specs(),
                file_store=file_store,
                template_renderer=template_renderer,
            )
        ),
    )


def build_sectioned_html_pdf_document_components(
    file_store,
    get_work_source=None,
    get_remedial_sheet_data=None,
    template_renderer=None,
    pdf_generator_factory=None,
    task_payload_formatter=None,
) -> SectionedDocumentComponents:
    components = build_sectioned_html_document_components(
        file_store=file_store,
        get_work_source=get_work_source,
        get_remedial_sheet_data=get_remedial_sheet_data,
        template_renderer=template_renderer,
        task_payload_formatter=task_payload_formatter,
    )
    pdf_renderer_registry = (
        build_template_sectioned_html_to_pdf_document_renderer_registry(
            renderer_type='pdf',
            renderer_specs=sectioned_html_renderer_specs(),
            file_store=file_store,
            template_renderer=template_renderer,
            pdf_generator_factory=pdf_generator_factory,
        )
    )
    components.document_renderer_registry.extend(pdf_renderer_registry)
    return components


def build_sectioned_document_components(
    file_store,
    get_work_source=None,
    get_remedial_sheet_data=None,
    template_renderer=None,
    pdf_generator_factory=None,
    task_payload_formatter=None,
) -> SectionedDocumentComponents:
    components = build_sectioned_html_pdf_document_components(
        file_store=file_store,
        get_work_source=get_work_source,
        get_remedial_sheet_data=get_remedial_sheet_data,
        template_renderer=template_renderer,
        pdf_generator_factory=pdf_generator_factory,
        task_payload_formatter=(
            task_payload_formatter
            or _sectioned_task_payload_formatter()
        ),
    )
    latex_renderer_registry = (
        build_template_sectioned_text_document_renderer_registry(
            renderer_type='latex',
            renderer_specs=sectioned_latex_renderer_specs(),
            file_store=file_store,
            template_renderer=template_renderer,
        )
    )
    components.document_renderer_registry.extend(latex_renderer_registry)
    return components


def build_sectioned_remedial_sheet_html_document_components(
    file_store,
    get_remedial_sheet_data=None,
    template_renderer=None,
) -> SectionedDocumentComponents:
    payload_registry = build_remedial_sheet_section_payload_builder_registry(
        get_remedial_sheet_data=get_remedial_sheet_data,
    )
    return SectionedDocumentComponents(
        document_builder=RecipeDocumentBuilder(
            section_payload_builder_registry=payload_registry,
        ),
        document_renderer_registry=(
            build_template_sectioned_text_document_renderer_registry(
                renderer_type='html',
                renderer_specs=remedial_html_renderer_specs(),
                file_store=file_store,
                template_renderer=template_renderer,
            )
        ),
    )


def build_sectioned_remedial_sheet_latex_document_components(
    file_store,
    get_remedial_sheet_data=None,
    template_renderer=None,
    task_payload_formatter=None,
) -> SectionedDocumentComponents:
    payload_registry = build_remedial_sheet_section_payload_builder_registry(
        get_remedial_sheet_data=get_remedial_sheet_data,
        task_payload_formatter=(
            task_payload_formatter or LatexTaskPayloadFormatter()
        ),
    )
    return SectionedDocumentComponents(
        document_builder=RecipeDocumentBuilder(
            section_payload_builder_registry=payload_registry,
        ),
        document_renderer_registry=(
            build_template_sectioned_text_document_renderer_registry(
                renderer_type='latex',
                renderer_specs=remedial_latex_renderer_specs(),
                file_store=file_store,
                template_renderer=template_renderer,
            )
        ),
    )


def _sectioned_task_payload_formatter():
    return RenderTargetTaskPayloadFormatter(
        formatters_by_renderer_type={
            'latex': LatexTaskPayloadFormatter(),
        },
    )
