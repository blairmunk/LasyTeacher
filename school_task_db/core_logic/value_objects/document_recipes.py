"""Default section recipes for generated documents."""

from collections.abc import Mapping, Sequence
from typing import Any

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentTemplateSpec,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetBuildOptions,
    WorkDocumentBuildOptions,
)


WORK_DOCUMENT_TYPE = 'work'
REMEDIAL_SHEET_DOCUMENT_TYPE = 'remedial_sheet'
WORKSHEET_DOCUMENT_TYPE = 'worksheet'
ANSWER_KEY_DOCUMENT_TYPE = 'answer_key'
HOMEWORK_DOCUMENT_TYPE = 'homework'
DIAGNOSTIC_DOCUMENT_TYPE = 'diagnostic'
CUSTOM_DOCUMENT_TYPE = 'custom'

HEADER_SECTION = 'header'
TASK_LIST_SECTION = 'task_list'
LEGACY_TASK_VARIANTS_SECTION = 'task_variants'
TASK_VARIANTS_SECTION = LEGACY_TASK_VARIANTS_SECTION
LEGACY_ANSWER_KEY_SECTION = 'answer_key'
ANSWER_KEY_SECTION = LEGACY_ANSWER_KEY_SECTION
ANSWERS_SECTION = 'answers'
SHORT_SOLUTIONS_SECTION = 'short_solutions'
FULL_SOLUTIONS_SECTION = 'full_solutions'
ORIGINAL_MISTAKES_SECTION = 'original_mistakes'
TRAINING_TASKS_SECTION = 'training_tasks'
THEORY_SECTION = 'theory'
PAGE_BREAK_SECTION = 'page_break'
SCORE_TABLE_SECTION = 'score_table'


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


def build_document_template_spec_from_config(
    name: str,
    template_type: str,
    sections_config: (
        Mapping[str, Any]
        | Sequence[Mapping[str, Any] | DocumentSectionSpec]
    ),
    default_content_config: Mapping[str, Any] | None = None,
) -> DocumentTemplateSpec:
    recipe = build_document_recipe_from_sections_config(
        document_type=template_type,
        sections_config=sections_config,
    )
    return DocumentTemplateSpec(
        name=name,
        template_type=template_type,
        sections=recipe.sections,
        default_content_config=default_content_config or {},
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


def build_work_document_recipe(
    options: WorkDocumentBuildOptions | None = None,
) -> DocumentRecipe:
    options = options or WorkDocumentBuildOptions()
    content_config = options.content_config
    sections = [
        DocumentSectionSpec(section_type=HEADER_SECTION),
        DocumentSectionSpec(
            section_type=TASK_LIST_SECTION,
            options={
                'include_hints': content_config['include_hints'],
                'include_instructions': content_config['include_instructions'],
            },
        ),
    ]

    if content_config['include_answers']:
        sections.append(DocumentSectionSpec(section_type=ANSWERS_SECTION))
    if content_config['include_short_solutions']:
        sections.append(DocumentSectionSpec(section_type=SHORT_SOLUTIONS_SECTION))
    if content_config['include_full_solutions']:
        sections.append(DocumentSectionSpec(section_type=FULL_SOLUTIONS_SECTION))

    return build_document_recipe_from_sections_config(
        document_type=WORK_DOCUMENT_TYPE,
        sections_config=sections,
    )


def build_remedial_sheet_document_recipe(
    options: RemedialSheetBuildOptions | None = None,
) -> DocumentRecipe:
    options = options or RemedialSheetBuildOptions()
    content_config = options.content_config
    sections = [
        DocumentSectionSpec(section_type=HEADER_SECTION),
        DocumentSectionSpec(
            section_type=ORIGINAL_MISTAKES_SECTION,
            options={'include_scores': True},
        ),
        DocumentSectionSpec(
            section_type=TRAINING_TASKS_SECTION,
            options={'include_scores': False},
        ),
    ]

    if content_config['include_answers']:
        sections.append(DocumentSectionSpec(section_type=ANSWERS_SECTION))
    if content_config['include_short_solutions']:
        sections.append(DocumentSectionSpec(section_type=SHORT_SOLUTIONS_SECTION))
    if content_config['include_full_solutions']:
        sections.append(DocumentSectionSpec(section_type=FULL_SOLUTIONS_SECTION))

    return build_document_recipe_from_sections_config(
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
        sections_config=sections,
    )
