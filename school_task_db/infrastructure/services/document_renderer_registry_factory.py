"""Factories for infrastructure document renderer registries."""

from core_logic.services.document_renderer_registry import DocumentRendererRegistry
from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)
from infrastructure.services.document_renderers import LegacyDocumentRenderer


def build_legacy_document_renderer_registry(
    document_from_paths,
    get_work_source,
    get_remedial_source,
    render_latex_work_files,
    render_html_work_files,
    render_pdf_work_files,
    render_remedial_latex_files,
    render_remedial_html_files,
    render_remedial_pdf_files,
) -> DocumentRendererRegistry:
    registry = DocumentRendererRegistry()
    _register_work_renderers(
        registry=registry,
        document_from_paths=document_from_paths,
        get_work_source=get_work_source,
        render_latex_work_files=render_latex_work_files,
        render_html_work_files=render_html_work_files,
        render_pdf_work_files=render_pdf_work_files,
    )
    _register_remedial_sheet_renderers(
        registry=registry,
        document_from_paths=document_from_paths,
        get_remedial_source=get_remedial_source,
        render_remedial_latex_files=render_remedial_latex_files,
        render_remedial_html_files=render_remedial_html_files,
        render_remedial_pdf_files=render_remedial_pdf_files,
    )
    return registry


def _register_work_renderers(
    registry,
    document_from_paths,
    get_work_source,
    render_latex_work_files,
    render_html_work_files,
    render_pdf_work_files,
) -> None:
    registry.register(
        'latex',
        LegacyDocumentRenderer(
            file_type='latex',
            source_getter=get_work_source,
            render_files=lambda work, content_config, render_target:
                render_latex_work_files(
                    work,
                    content_config,
                    render_target.page_format,
                ),
            document_from_paths=document_from_paths,
        ),
        document_type=WORK_DOCUMENT_TYPE,
    )
    registry.register(
        'html',
        LegacyDocumentRenderer(
            file_type='html',
            source_getter=get_work_source,
            render_files=lambda work, content_config, render_target:
                render_html_work_files(work, content_config),
            document_from_paths=document_from_paths,
        ),
        document_type=WORK_DOCUMENT_TYPE,
    )
    registry.register(
        'pdf',
        LegacyDocumentRenderer(
            file_type='pdf',
            source_getter=get_work_source,
            render_files=lambda work, content_config, render_target:
                render_pdf_work_files(
                    work,
                    content_config,
                    render_target.page_format,
                ),
            document_from_paths=document_from_paths,
        ),
        document_type=WORK_DOCUMENT_TYPE,
    )


def _register_remedial_sheet_renderers(
    registry,
    document_from_paths,
    get_remedial_source,
    render_remedial_latex_files,
    render_remedial_html_files,
    render_remedial_pdf_files,
) -> None:
    registry.register(
        'latex',
        LegacyDocumentRenderer(
            file_type='latex',
            source_getter=get_remedial_source,
            render_files=lambda variant, content_config, render_target:
                render_remedial_latex_files(
                    variant,
                    content_config,
                    render_target.page_format,
                ),
            document_from_paths=document_from_paths,
        ),
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
    )
    registry.register(
        'html',
        LegacyDocumentRenderer(
            file_type='html',
            source_getter=get_remedial_source,
            render_files=lambda variant, content_config, render_target:
                render_remedial_html_files(variant, content_config),
            document_from_paths=document_from_paths,
        ),
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
    )
    registry.register(
        'pdf',
        LegacyDocumentRenderer(
            file_type='pdf',
            source_getter=get_remedial_source,
            render_files=lambda variant, content_config, render_target:
                render_remedial_pdf_files(
                    variant,
                    content_config,
                    render_target.page_format,
                ),
            document_from_paths=document_from_paths,
        ),
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
    )
