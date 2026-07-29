"""Default section recipes for generated documents."""

from collections.abc import Mapping, Sequence
from typing import Any

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
)


WORK_DOCUMENT_TYPE = 'work'
REMEDIAL_SHEET_DOCUMENT_TYPE = 'remedial_sheet'
WORKSHEET_DOCUMENT_TYPE = 'worksheet'
ANSWER_KEY_DOCUMENT_TYPE = 'answer_key'
HOMEWORK_DOCUMENT_TYPE = 'homework'
DIAGNOSTIC_DOCUMENT_TYPE = 'diagnostic'
CUSTOM_DOCUMENT_TYPE = 'custom'

HEADER_SECTION = 'header'
COMMON_HEADER_SECTION = 'common_header'
TASK_LIST_SECTION = 'task_list'
ANSWER_KEY_SECTION = 'answer_key'
ANSWERS_SECTION = 'answers'
SHORT_SOLUTIONS_SECTION = 'short_solutions'
FULL_SOLUTIONS_SECTION = 'full_solutions'
ORIGINAL_MISTAKES_SECTION = 'original_mistakes'
TRAINING_TASKS_SECTION = 'training_tasks'
PAGE_BREAK_SECTION = 'page_break'
SCORE_TABLE_SECTION = 'score_table'
BLANK_CELLS_SECTION = 'blank_cells'


def build_document_recipe_from_sections_config(
    document_type: str,
    sections_config: (
        Mapping[str, Any]
        | Sequence[Mapping[str, Any] | DocumentSectionSpec]
    ),
) -> DocumentRecipe:
    """Build a recipe from a JSON-like sections configuration."""
    if isinstance(sections_config, Mapping):
        sections_config = sections_config.get('sections', ())

    return DocumentRecipe(
        document_type=document_type,
        sections=[
            _section_spec_from_config(section_config)
            for section_config in sections_config
        ],
    )


def _section_spec_from_config(
    section_config: Mapping[str, Any] | DocumentSectionSpec,
) -> DocumentSectionSpec:
    if isinstance(section_config, DocumentSectionSpec):
        return section_config

    section_type = (
        section_config.get('type')
        or section_config.get('section_type')
        or ''
    )
    options = section_config.get('params', section_config.get('options', {}))
    if options is None:
        options = {}
    if not isinstance(options, Mapping):
        raise ValueError('section params must be a mapping')

    return DocumentSectionSpec(
        section_type=section_type,
        title=section_config.get('title', ''),
        options=dict(options),
    )
