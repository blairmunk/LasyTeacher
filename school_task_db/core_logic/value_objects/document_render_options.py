from dataclasses import dataclass
from typing import Mapping


ANSWER_TYPES_WITH_ANSWERS = {
    'with_answers',
    'with_short_solutions',
    'with_full_solutions',
}

FILE_TYPE_LABELS = {
    'latex': 'LaTeX',
    'html': 'HTML',
    'pdf': 'PDF',
}
SUPPORTED_DOCUMENT_RENDERER_TYPES = frozenset(FILE_TYPE_LABELS)


def is_supported_document_renderer_type(renderer_type: str) -> bool:
    return renderer_type in SUPPORTED_DOCUMENT_RENDERER_TYPES


@dataclass(frozen=True)
class RenderTarget:
    renderer_type: str = 'pdf'
    page_format: str = 'A4'

    @property
    def file_type_label(self) -> str:
        return FILE_TYPE_LABELS[self.renderer_type]


def build_render_target_from_data(
    data: Mapping[str, str],
    default_renderer_type: str = 'pdf',
) -> RenderTarget:
    return RenderTarget(
        renderer_type=renderer_type_from_data(data, default_renderer_type),
        page_format=data.get('format', 'A4'),
    )


@dataclass(frozen=True)
class WorkDocumentPrintOverrides:
    """Temporary changes applied to one document render request."""

    hide_theory: bool = False
    hide_text: bool = False
    hide_blank_cells: bool = False
    append_answers: bool = False
    break_between_variants: bool = True

    @property
    def hidden_content_types(self) -> tuple[str, ...]:
        hidden_types = []
        if self.hide_theory:
            hidden_types.append('theory')
        if self.hide_text:
            hidden_types.append('text')
        return tuple(hidden_types)


@dataclass(frozen=True)
class RemedialSheetBuildOptions:
    answer_type: str = 'with_short_solutions'

    @property
    def content_config(self) -> dict:
        return {
            'include_answers': self.answer_type in ANSWER_TYPES_WITH_ANSWERS,
            'include_short_solutions': self.answer_type in {
                'with_short_solutions',
                'with_full_solutions',
            },
            'include_full_solutions': self.answer_type == 'with_full_solutions',
        }


def build_work_print_overrides_from_data(
    data: Mapping[str, str],
) -> WorkDocumentPrintOverrides:
    return WorkDocumentPrintOverrides(
        break_between_variants=data.get('break_between_variants', '1') == '1',
        hide_theory=data.get('hide_theory', '0') == '1',
        hide_text=data.get('hide_text', '0') == '1',
        hide_blank_cells=data.get('hide_blank_cells', '0') == '1',
        append_answers=data.get('append_answers', '0') == '1',
    )


def build_remedial_sheet_build_options_from_data(
    data: Mapping[str, str],
) -> RemedialSheetBuildOptions:
    return RemedialSheetBuildOptions(
        answer_type=data.get('answer_type', 'with_short_solutions'),
    )


def renderer_type_from_data(data: Mapping[str, str], default='pdf') -> str:
    return data.get('renderer_type', default)
