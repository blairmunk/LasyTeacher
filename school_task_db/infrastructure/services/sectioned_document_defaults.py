"""Default component wiring for section-based document rendering."""

from dataclasses import dataclass

from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.services.document_renderer_registry import DocumentRendererRegistry
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_VARIANTS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from infrastructure.services.django_document_section_payloads import (
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


def work_html_filename(request):
    if request.document.source and request.document.source.source_id:
        return f'work_{request.document.source.source_id}.html'
    return 'work.html'
