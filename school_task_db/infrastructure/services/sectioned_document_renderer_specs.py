"""Built-in renderer specs for sectioned documents."""

from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    STUDENT_DIGEST_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)
from infrastructure.services.sectioned_document_filenames import (
    event_report_html_filename,
    remedial_html_filename,
    remedial_latex_filename,
    student_digest_html_filename,
    work_html_filename,
    work_latex_filename,
)
from infrastructure.services.sectioned_document_renderer_factory import (
    TemplateSectionedTextDocumentRendererSpec,
)
from infrastructure.services.sectioned_document_templates import (
    EVENT_REPORT_HTML_SECTION_TEMPLATES,
    REMEDIAL_HTML_SECTION_TEMPLATES,
    REMEDIAL_HTML_WRAPPER_TEMPLATE,
    REMEDIAL_LATEX_SECTION_TEMPLATES,
    REMEDIAL_LATEX_WRAPPER_TEMPLATE,
    REPORT_HTML_WRAPPER_TEMPLATE,
    STUDENT_DIGEST_HTML_SECTION_TEMPLATES,
    WORK_HTML_SECTION_TEMPLATES,
    WORK_HTML_WRAPPER_TEMPLATE,
    WORK_LATEX_SECTION_TEMPLATES,
    WORK_LATEX_WRAPPER_TEMPLATE,
)


def sectioned_html_renderer_specs():
    return (
        work_html_renderer_specs()
        + remedial_html_renderer_specs()
        + report_html_renderer_specs()
    )


def sectioned_latex_renderer_specs():
    return work_latex_renderer_specs() + remedial_latex_renderer_specs()


def work_html_renderer_specs():
    return [
        TemplateSectionedTextDocumentRendererSpec(
            document_type=WORK_DOCUMENT_TYPE,
            section_templates=WORK_HTML_SECTION_TEMPLATES,
            filename_builder=work_html_filename,
            wrapper_template_name=WORK_HTML_WRAPPER_TEMPLATE,
        ),
    ]


def work_latex_renderer_specs():
    return [
        TemplateSectionedTextDocumentRendererSpec(
            document_type=WORK_DOCUMENT_TYPE,
            section_templates=WORK_LATEX_SECTION_TEMPLATES,
            filename_builder=work_latex_filename,
            wrapper_template_name=WORK_LATEX_WRAPPER_TEMPLATE,
        ),
    ]


def remedial_html_renderer_specs():
    return [
        TemplateSectionedTextDocumentRendererSpec(
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            section_templates=REMEDIAL_HTML_SECTION_TEMPLATES,
            filename_builder=remedial_html_filename,
            wrapper_template_name=REMEDIAL_HTML_WRAPPER_TEMPLATE,
        ),
    ]


def remedial_latex_renderer_specs():
    return [
        TemplateSectionedTextDocumentRendererSpec(
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            section_templates=REMEDIAL_LATEX_SECTION_TEMPLATES,
            filename_builder=remedial_latex_filename,
            wrapper_template_name=REMEDIAL_LATEX_WRAPPER_TEMPLATE,
        ),
    ]


def report_html_renderer_specs():
    return [
        TemplateSectionedTextDocumentRendererSpec(
            document_type=EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
            section_templates=EVENT_REPORT_HTML_SECTION_TEMPLATES,
            filename_builder=event_report_html_filename,
            wrapper_template_name=REPORT_HTML_WRAPPER_TEMPLATE,
        ),
        TemplateSectionedTextDocumentRendererSpec(
            document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
            section_templates=STUDENT_DIGEST_HTML_SECTION_TEMPLATES,
            filename_builder=student_digest_html_filename,
            wrapper_template_name=REPORT_HTML_WRAPPER_TEMPLATE,
        ),
    ]
