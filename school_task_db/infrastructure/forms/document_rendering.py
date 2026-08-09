"""Parse HTTP form values into document rendering value objects."""

from collections.abc import Mapping

from core_logic.value_objects.document_render_options import (
    RemedialSheetPrintOptions,
    RenderTarget,
    WorkDocumentPrintOverrides,
)


def render_target_from_data(
    data: Mapping[str, str],
    default_renderer_type: str = 'pdf',
) -> RenderTarget:
    return RenderTarget(
        renderer_type=renderer_type_from_data(data, default_renderer_type),
        page_format=data.get('format', 'A4'),
    )


def work_print_overrides_from_data(
    data: Mapping[str, str],
) -> WorkDocumentPrintOverrides:
    return WorkDocumentPrintOverrides(
        break_between_variants=data.get('break_between_variants', '1') == '1',
        hide_theory=data.get('hide_theory', '0') == '1',
        hide_text=data.get('hide_text', '0') == '1',
        hide_blank_cells=data.get('hide_blank_cells', '0') == '1',
        append_answers=data.get('append_answers', '0') == '1',
    )


def remedial_sheet_print_options_from_data(
    data: Mapping[str, str],
) -> RemedialSheetPrintOptions:
    return RemedialSheetPrintOptions(
        answer_type=data.get('answer_type', 'with_short_solutions'),
    )


def renderer_type_from_data(data: Mapping[str, str], default='pdf') -> str:
    return data.get('renderer_type', default)
