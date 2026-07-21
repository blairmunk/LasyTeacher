"""Factories for default document recipes."""

from core_logic.entities.document import DocumentRecipe, DocumentSectionSpec
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
    build_document_recipe_from_sections_config,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetBuildOptions,
    WorkDocumentBuildOptions,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_DEMO,
    TASK_BANK_ROLE_PRACTICE,
    TASK_RENDER_MODE_TASK_ONLY,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
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


def build_worksheet_work_document_recipe(
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
                'role_render_modes': {
                    TASK_BANK_ROLE_DEMO: TASK_RENDER_MODE_WITH_FULL_SOLUTION,
                    TASK_BANK_ROLE_PRACTICE: TASK_RENDER_MODE_TASK_ONLY,
                },
                'role_blank_cells': {
                    TASK_BANK_ROLE_PRACTICE: {
                        'rows': DEFAULT_BLANK_CELLS_ROWS,
                    },
                },
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
