from dataclasses import dataclass
from typing import Mapping, Optional


ANSWER_TYPES_WITH_ANSWERS = {
    'with_answers',
    'with_short_solutions',
    'with_full_solutions',
}

CONTENT_DESCRIPTIONS = {
    'tasks_only': 'только задания',
    'with_answers': 'с ответами',
    'with_short_solutions': 'с краткими решениями',
    'with_full_solutions': 'с полными решениями',
}

FILE_TYPE_LABELS = {
    'latex': 'LaTeX',
    'html': 'HTML',
    'pdf': 'PDF',
}


@dataclass(frozen=True, init=False)
class WorkDocumentRenderOptions:
    renderer_type: str = 'pdf'
    pdf_format: str = 'A4'
    answer_type: str = 'tasks_only'
    include_hints: bool = False
    include_instructions: bool = False

    def __init__(
        self,
        renderer_type: Optional[str] = None,
        pdf_format: str = 'A4',
        answer_type: str = 'tasks_only',
        include_hints: bool = False,
        include_instructions: bool = False,
        generator_type: Optional[str] = None,
    ):
        object.__setattr__(
            self,
            'renderer_type',
            renderer_type or generator_type or 'pdf',
        )
        object.__setattr__(self, 'pdf_format', pdf_format)
        object.__setattr__(self, 'answer_type', answer_type)
        object.__setattr__(self, 'include_hints', include_hints)
        object.__setattr__(self, 'include_instructions', include_instructions)

    @property
    def generator_type(self) -> str:
        return self.renderer_type

    @property
    def content_config(self) -> dict:
        return {
            'include_answers': self.answer_type in ANSWER_TYPES_WITH_ANSWERS,
            'include_short_solutions': self.answer_type in {
                'with_short_solutions',
                'with_full_solutions',
            },
            'include_full_solutions': self.answer_type == 'with_full_solutions',
            'answer_type': self.answer_type,
            'include_hints': self.include_hints,
            'include_instructions': self.include_instructions,
        }

    @property
    def file_type_label(self) -> str:
        return FILE_TYPE_LABELS[self.renderer_type]

    @property
    def content_description(self) -> str:
        base_description = CONTENT_DESCRIPTIONS[self.answer_type]
        additional_content = []
        if self.include_hints:
            additional_content.append('подсказки')
        if self.include_instructions:
            additional_content.append('инструкции')

        if not additional_content:
            return base_description

        return f"{base_description} + {' + '.join(additional_content)}"


@dataclass(frozen=True, init=False)
class RemedialSheetDocumentRenderOptions:
    renderer_type: str = 'pdf'
    pdf_format: str = 'A4'
    answer_type: str = 'with_short_solutions'

    def __init__(
        self,
        renderer_type: Optional[str] = None,
        pdf_format: str = 'A4',
        answer_type: str = 'with_short_solutions',
        generator_type: Optional[str] = None,
    ):
        object.__setattr__(
            self,
            'renderer_type',
            renderer_type or generator_type or 'pdf',
        )
        object.__setattr__(self, 'pdf_format', pdf_format)
        object.__setattr__(self, 'answer_type', answer_type)

    @property
    def generator_type(self) -> str:
        return self.renderer_type

    @property
    def content_config(self) -> dict:
        return {
            'include_answers': self.answer_type in ANSWER_TYPES_WITH_ANSWERS,
            'include_short_solutions': self.answer_type in {
                'with_short_solutions',
                'with_full_solutions',
            },
            'include_full_solutions': self.answer_type == 'with_full_solutions',
            'page_format': self.pdf_format,
        }


WorkGenerationOptions = WorkDocumentRenderOptions
RemedialSheetGenerationOptions = RemedialSheetDocumentRenderOptions


def build_work_generation_options(
    data: Mapping[str, str],
) -> WorkDocumentRenderOptions:
    answer_type = data.get('answer_type', 'tasks_only')
    if data.get('with_answers', '0') == '1' and answer_type == 'tasks_only':
        answer_type = 'with_answers'

    return WorkDocumentRenderOptions(
        renderer_type=(
            data.get('renderer_type')
            or data.get('generator_type', 'pdf')
        ),
        pdf_format=data.get('format', 'A4'),
        answer_type=answer_type,
        include_hints=data.get('include_hints', '0') == '1',
        include_instructions=data.get('include_instructions', '0') == '1',
    )


def build_remedial_sheet_generation_options(
    data: Mapping[str, str],
) -> RemedialSheetDocumentRenderOptions:
    return RemedialSheetDocumentRenderOptions(
        renderer_type=(
            data.get('renderer_type')
            or data.get('generator_type', 'pdf')
        ),
        pdf_format=data.get('format', 'A4'),
        answer_type=data.get('answer_type', 'with_short_solutions'),
    )
