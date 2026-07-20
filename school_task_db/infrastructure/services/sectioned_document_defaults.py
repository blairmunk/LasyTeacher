"""Default component wiring for section-based document rendering."""

from dataclasses import dataclass

from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.services.document_renderer_registry import DocumentRendererRegistry
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    TASK_VARIANTS_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from infrastructure.services.django_document_section_payloads import (
    build_remedial_sheet_section_payload_builder_registry,
    build_work_section_payload_builder_registry,
)
from infrastructure.services.sectioned_document_renderer_factory import (
    TemplateSectionedTextDocumentRendererSpec,
    build_template_sectioned_text_document_renderer_registry,
)


WORK_HTML_SECTION_TEMPLATES = {
    HEADER_SECTION: 'documents/html/sections/header.html',
    TASK_VARIANTS_SECTION: 'documents/html/sections/task_variants.html',
    ANSWERS_SECTION: 'documents/html/sections/answers.html',
    SHORT_SOLUTIONS_SECTION: 'documents/html/sections/short_solutions.html',
    FULL_SOLUTIONS_SECTION: 'documents/html/sections/full_solutions.html',
}
WORK_HTML_WRAPPER_TEMPLATE = 'documents/html/base/document.html'
REMEDIAL_HTML_SECTION_TEMPLATES = {
    HEADER_SECTION: 'documents/html/sections/remedial_header.html',
    ORIGINAL_MISTAKES_SECTION: (
        'documents/html/sections/remedial_original_mistakes.html'
    ),
    TRAINING_TASKS_SECTION: (
        'documents/html/sections/remedial_training_tasks.html'
    ),
    ANSWERS_SECTION: 'documents/html/sections/remedial_answers.html',
    SHORT_SOLUTIONS_SECTION: (
        'documents/html/sections/remedial_short_solutions.html'
    ),
    FULL_SOLUTIONS_SECTION: (
        'documents/html/sections/remedial_full_solutions.html'
    ),
}
REMEDIAL_HTML_WRAPPER_TEMPLATE = 'documents/html/base/document.html'


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
                renderer_specs=[
                    TemplateSectionedTextDocumentRendererSpec(
                        document_type=WORK_DOCUMENT_TYPE,
                        section_templates=WORK_HTML_SECTION_TEMPLATES,
                        filename_builder=work_html_filename,
                        wrapper_template_name=WORK_HTML_WRAPPER_TEMPLATE,
                    ),
                ],
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
) -> SectionedDocumentComponents:
    payload_registry = build_work_section_payload_builder_registry(
        get_work_source=get_work_source,
    )
    payload_registry.extend(
        build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=get_remedial_sheet_data,
        )
    )
    return SectionedDocumentComponents(
        document_builder=RecipeDocumentBuilder(
            section_payload_builder_registry=payload_registry,
        ),
        document_renderer_registry=(
            build_template_sectioned_text_document_renderer_registry(
                renderer_type='html',
                renderer_specs=[
                    TemplateSectionedTextDocumentRendererSpec(
                        document_type=WORK_DOCUMENT_TYPE,
                        section_templates=WORK_HTML_SECTION_TEMPLATES,
                        filename_builder=work_html_filename,
                        wrapper_template_name=WORK_HTML_WRAPPER_TEMPLATE,
                    ),
                    TemplateSectionedTextDocumentRendererSpec(
                        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        section_templates=REMEDIAL_HTML_SECTION_TEMPLATES,
                        filename_builder=remedial_html_filename,
                        wrapper_template_name=REMEDIAL_HTML_WRAPPER_TEMPLATE,
                    ),
                ],
                file_store=file_store,
                template_renderer=template_renderer,
            )
        ),
    )


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
                renderer_specs=[
                    TemplateSectionedTextDocumentRendererSpec(
                        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        section_templates=REMEDIAL_HTML_SECTION_TEMPLATES,
                        filename_builder=remedial_html_filename,
                        wrapper_template_name=REMEDIAL_HTML_WRAPPER_TEMPLATE,
                    ),
                ],
                file_store=file_store,
                template_renderer=template_renderer,
            )
        ),
    )


def work_html_filename(request):
    if request.document.source and request.document.source.source_id:
        return f'work_{request.document.source.source_id}.html'
    return 'work.html'


def remedial_html_filename(request):
    if request.document.source and request.document.source.source_id:
        return f'remedial_{request.document.source.source_id}.html'
    return 'remedial.html'
