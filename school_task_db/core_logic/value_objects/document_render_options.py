from dataclasses import dataclass


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


@dataclass(frozen=True)
class WorkDocumentPrintOverrides:
    """Temporary changes applied to one document render request."""

    hide_theory: bool = False
    hide_text: bool = False
    hide_blank_cells: bool = False
    append_answers: bool = False
    break_between_variants: bool = True
    include_task_page_breaks: bool = True

    @property
    def hidden_content_types(self) -> tuple[str, ...]:
        hidden_types = []
        if self.hide_theory:
            hidden_types.append('theory')
        if self.hide_text:
            hidden_types.append('text')
        return tuple(hidden_types)


@dataclass(frozen=True)
class RemedialSheetPrintOptions:
    """Temporary presentation choices for a personalized remedial sheet."""

    answer_type: str = 'with_short_solutions'

    @property
    def include_answers(self) -> bool:
        return self.answer_type in ANSWER_TYPES_WITH_ANSWERS

    @property
    def include_short_solutions(self) -> bool:
        return self.answer_type in {
            'with_short_solutions',
            'with_full_solutions',
        }

    @property
    def include_full_solutions(self) -> bool:
        return self.answer_type == 'with_full_solutions'
