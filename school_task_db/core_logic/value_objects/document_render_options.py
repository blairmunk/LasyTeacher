from dataclasses import dataclass
from typing import Mapping, Optional


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


def build_render_target(
    renderer_type: Optional[str] = None,
    pdf_format: str = 'A4',
    render_target: Optional[RenderTarget] = None,
) -> RenderTarget:
    return render_target or RenderTarget(
        renderer_type=renderer_type or 'pdf',
        page_format=pdf_format,
    )


def build_render_target_from_data(
    data: Mapping[str, str],
    default_renderer_type: str = 'pdf',
) -> RenderTarget:
    return build_render_target(
        renderer_type=renderer_type_from_data(data, default_renderer_type),
        pdf_format=data.get('format', 'A4'),
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


@dataclass(frozen=True, init=False)
class WorkDocumentRenderOptions:
    render_target: RenderTarget
    print_overrides: WorkDocumentPrintOverrides

    def __init__(
        self,
        renderer_type: Optional[str] = None,
        pdf_format: str = 'A4',
        break_between_variants: bool = True,
        hide_theory: bool = False,
        hide_text: bool = False,
        hide_blank_cells: bool = False,
        append_answers: bool = False,
        render_target: Optional[RenderTarget] = None,
        print_overrides: Optional[WorkDocumentPrintOverrides] = None,
    ):
        object.__setattr__(
            self,
            'render_target',
            build_render_target(
                renderer_type=renderer_type,
                pdf_format=pdf_format,
                render_target=render_target,
            ),
        )
        object.__setattr__(
            self,
            'print_overrides',
            print_overrides or WorkDocumentPrintOverrides(
                hide_theory=hide_theory,
                hide_text=hide_text,
                hide_blank_cells=hide_blank_cells,
                append_answers=append_answers,
                break_between_variants=break_between_variants,
            ),
        )

    @property
    def renderer_type(self) -> str:
        return self.render_target.renderer_type

    @property
    def pdf_format(self) -> str:
        return self.render_target.page_format

    @property
    def break_between_variants(self) -> bool:
        return self.print_overrides.break_between_variants

    @property
    def file_type_label(self) -> str:
        return self.render_target.file_type_label

    @property
    def content_description(self) -> str:
        if self.print_overrides.append_answers:
            return 'по спецификации + ответы в конце'
        return 'по спецификации'


@dataclass(frozen=True, init=False)
class RemedialSheetDocumentRenderOptions:
    render_target: RenderTarget
    build_options: RemedialSheetBuildOptions

    def __init__(
        self,
        renderer_type: Optional[str] = None,
        pdf_format: str = 'A4',
        answer_type: str = 'with_short_solutions',
        render_target: Optional[RenderTarget] = None,
        build_options: Optional[RemedialSheetBuildOptions] = None,
    ):
        object.__setattr__(
            self,
            'render_target',
            build_render_target(
                renderer_type=renderer_type,
                pdf_format=pdf_format,
                render_target=render_target,
            ),
        )
        object.__setattr__(
            self,
            'build_options',
            build_options or RemedialSheetBuildOptions(answer_type=answer_type),
        )

    @property
    def renderer_type(self) -> str:
        return self.render_target.renderer_type

    @property
    def pdf_format(self) -> str:
        return self.render_target.page_format

    @property
    def answer_type(self) -> str:
        return self.build_options.answer_type

    @property
    def content_config(self) -> dict:
        return {
            **self.build_options.content_config,
            'page_format': self.pdf_format,
        }


def build_work_render_options(
    data: Mapping[str, str],
) -> WorkDocumentRenderOptions:
    return WorkDocumentRenderOptions(
        render_target=build_render_target_from_data(data),
        break_between_variants=data.get('break_between_variants', '1') == '1',
        hide_theory=data.get('hide_theory', '0') == '1',
        hide_text=data.get('hide_text', '0') == '1',
        hide_blank_cells=data.get('hide_blank_cells', '0') == '1',
        append_answers=data.get('append_answers', '0') == '1',
    )


def build_remedial_sheet_render_options(
    data: Mapping[str, str],
) -> RemedialSheetDocumentRenderOptions:
    return RemedialSheetDocumentRenderOptions(
        render_target=build_render_target_from_data(data),
        answer_type=data.get('answer_type', 'with_short_solutions'),
    )


def renderer_type_from_data(data: Mapping[str, str], default='pdf') -> str:
    return data.get('renderer_type', default)
