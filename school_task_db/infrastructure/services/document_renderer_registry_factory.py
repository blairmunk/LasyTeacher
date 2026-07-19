"""Factories for infrastructure document renderer registries."""

from core_logic.services.document_renderer_registry import DocumentRendererRegistry
from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)
from infrastructure.services.document_renderers import LegacyDocumentRenderer
from works.models import Variant, Work


def build_legacy_document_renderer_registry(
    document_from_paths,
    generate_latex_work,
    generate_html_work,
    generate_pdf_work,
    generate_remedial_latex,
    generate_remedial_html,
    generate_remedial_pdf,
) -> DocumentRendererRegistry:
    registry = DocumentRendererRegistry()
    _register_work_renderers(
        registry=registry,
        document_from_paths=document_from_paths,
        generate_latex_work=generate_latex_work,
        generate_html_work=generate_html_work,
        generate_pdf_work=generate_pdf_work,
    )
    _register_remedial_sheet_renderers(
        registry=registry,
        document_from_paths=document_from_paths,
        generate_remedial_latex=generate_remedial_latex,
        generate_remedial_html=generate_remedial_html,
        generate_remedial_pdf=generate_remedial_pdf,
    )
    return registry


def _register_work_renderers(
    registry,
    document_from_paths,
    generate_latex_work,
    generate_html_work,
    generate_pdf_work,
) -> None:
    registry.register(
        'latex',
        LegacyDocumentRenderer(
            file_type='latex',
            source_getter=lambda source_id: Work.objects.get(pk=source_id),
            render_files=lambda work, content_config, render_target:
                generate_latex_work(
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
            source_getter=lambda source_id: Work.objects.get(pk=source_id),
            render_files=lambda work, content_config, render_target:
                generate_html_work(work, content_config),
            document_from_paths=document_from_paths,
        ),
        document_type=WORK_DOCUMENT_TYPE,
    )
    registry.register(
        'pdf',
        LegacyDocumentRenderer(
            file_type='pdf',
            source_getter=lambda source_id: Work.objects.get(pk=source_id),
            render_files=lambda work, content_config, render_target:
                generate_pdf_work(
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
    generate_remedial_latex,
    generate_remedial_html,
    generate_remedial_pdf,
) -> None:
    registry.register(
        'latex',
        LegacyDocumentRenderer(
            file_type='latex',
            source_getter=lambda source_id: Variant.objects.get(pk=source_id),
            render_files=lambda variant, content_config, render_target:
                generate_remedial_latex(
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
            source_getter=lambda source_id: Variant.objects.get(pk=source_id),
            render_files=lambda variant, content_config, render_target:
                generate_remedial_html(variant, content_config),
            document_from_paths=document_from_paths,
        ),
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
    )
    registry.register(
        'pdf',
        LegacyDocumentRenderer(
            file_type='pdf',
            source_getter=lambda source_id: Variant.objects.get(pk=source_id),
            render_files=lambda variant, content_config, render_target:
                generate_remedial_pdf(
                    variant,
                    content_config,
                    render_target.page_format,
                ),
            document_from_paths=document_from_paths,
        ),
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
    )
