"""Default component wiring for section-based document rendering."""

from dataclasses import dataclass

from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.services.document_renderer_registry import DocumentRendererRegistry
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TASK_VARIANTS_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from infrastructure.services.django_document_section_payloads import (
    build_remedial_sheet_section_payload_builder_registry,
    build_work_section_payload_builder_registry,
)
from infrastructure.services.document_renderer_registry_factory import (
    build_legacy_document_renderer_registry_from_adapters,
)
from infrastructure.services.latex_document_payloads import (
    LatexTaskPayloadFormatter,
)
from infrastructure.services.sectioned_document_renderer_factory import (
    TemplateSectionedTextDocumentRendererSpec,
    build_template_sectioned_html_to_pdf_document_renderer_registry,
    build_template_sectioned_text_document_renderer_registry,
)


WORK_HTML_SECTION_TEMPLATES = {
    HEADER_SECTION: 'documents/html/sections/header.html',
    TASK_LIST_SECTION: 'documents/html/sections/task_variants.html',
    TASK_VARIANTS_SECTION: 'documents/html/sections/task_variants.html',
    ANSWER_KEY_SECTION: 'documents/html/sections/answers.html',
    ANSWERS_SECTION: 'documents/html/sections/answers.html',
    SHORT_SOLUTIONS_SECTION: 'documents/html/sections/short_solutions.html',
    FULL_SOLUTIONS_SECTION: 'documents/html/sections/full_solutions.html',
}
WORK_HTML_WRAPPER_TEMPLATE = 'documents/html/base/document.html'
WORK_LATEX_SECTION_TEMPLATES = {
    HEADER_SECTION: 'documents/latex/sections/header.tex',
    TASK_LIST_SECTION: 'documents/latex/sections/task_variants.tex',
    TASK_VARIANTS_SECTION: 'documents/latex/sections/task_variants.tex',
    ANSWER_KEY_SECTION: 'documents/latex/sections/answers.tex',
    ANSWERS_SECTION: 'documents/latex/sections/answers.tex',
    SHORT_SOLUTIONS_SECTION: 'documents/latex/sections/short_solutions.tex',
    FULL_SOLUTIONS_SECTION: 'documents/latex/sections/full_solutions.tex',
}
WORK_LATEX_WRAPPER_TEMPLATE = 'documents/latex/base/document.tex'
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
                renderer_specs=[
                    TemplateSectionedTextDocumentRendererSpec(
                        document_type=WORK_DOCUMENT_TYPE,
                        section_templates=WORK_LATEX_SECTION_TEMPLATES,
                        filename_builder=work_latex_filename,
                        wrapper_template_name=WORK_LATEX_WRAPPER_TEMPLATE,
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
                renderer_specs=_sectioned_html_renderer_specs(),
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
) -> SectionedDocumentComponents:
    components = build_sectioned_html_document_components(
        file_store=file_store,
        get_work_source=get_work_source,
        get_remedial_sheet_data=get_remedial_sheet_data,
        template_renderer=template_renderer,
    )
    pdf_renderer_registry = (
        build_template_sectioned_html_to_pdf_document_renderer_registry(
            renderer_type='pdf',
            renderer_specs=_sectioned_html_renderer_specs(),
            file_store=file_store,
            template_renderer=template_renderer,
            pdf_generator_factory=pdf_generator_factory,
        )
    )
    components.document_renderer_registry.extend(pdf_renderer_registry)
    return components


def build_legacy_with_sectioned_document_components(
    file_store,
    get_work_source,
    get_remedial_source,
    legacy_file_renderer,
    get_remedial_sheet_data=None,
    template_renderer=None,
    pdf_generator_factory=None,
) -> SectionedDocumentComponents:
    sectioned_components = build_sectioned_html_pdf_document_components(
        file_store=file_store,
        get_work_source=get_work_source,
        get_remedial_sheet_data=get_remedial_sheet_data,
        template_renderer=template_renderer,
        pdf_generator_factory=pdf_generator_factory,
    )
    renderer_registry = build_legacy_document_renderer_registry_from_adapters(
        file_store=file_store,
        get_work_source=get_work_source,
        get_remedial_source=get_remedial_source,
        legacy_file_renderer=legacy_file_renderer,
    )
    renderer_registry.extend(sectioned_components.document_renderer_registry)
    return SectionedDocumentComponents(
        document_builder=sectioned_components.document_builder,
        document_renderer_registry=renderer_registry,
    )


def build_legacy_with_sectioned_html_document_components(
    file_store,
    get_work_source,
    get_remedial_source,
    legacy_file_renderer,
    get_remedial_sheet_data=None,
    template_renderer=None,
    pdf_generator_factory=None,
) -> SectionedDocumentComponents:
    return build_legacy_with_sectioned_document_components(
        file_store=file_store,
        get_work_source=get_work_source,
        get_remedial_source=get_remedial_source,
        legacy_file_renderer=legacy_file_renderer,
        get_remedial_sheet_data=get_remedial_sheet_data,
        template_renderer=template_renderer,
        pdf_generator_factory=pdf_generator_factory,
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


def work_latex_filename(request):
    if request.document.source and request.document.source.source_id:
        return f'work_{request.document.source.source_id}.tex'
    return 'work.tex'


def _sectioned_html_renderer_specs():
    return [
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
    ]
