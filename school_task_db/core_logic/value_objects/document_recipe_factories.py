"""Factories for default document recipes."""

from core_logic.entities.document import DocumentRecipe, DocumentSectionSpec
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    PAGE_BREAK_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetBuildOptions,
)


def build_work_document_recipe() -> DocumentRecipe:
    sections = [
        DocumentSectionSpec(section_type=HEADER_SECTION),
        DocumentSectionSpec(section_type=TASK_LIST_SECTION),
    ]

    return DocumentRecipe(
        document_type=WORK_DOCUMENT_TYPE,
        sections=sections,
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
        DocumentSectionSpec(section_type=PAGE_BREAK_SECTION),
        DocumentSectionSpec(
            section_type=TRAINING_TASKS_SECTION,
            options={'include_scores': False},
        ),
    ]

    if content_config['include_answers']:
        sections.extend((
            DocumentSectionSpec(section_type=PAGE_BREAK_SECTION),
            DocumentSectionSpec(section_type=ANSWERS_SECTION),
        ))
    if content_config['include_short_solutions']:
        sections.extend((
            DocumentSectionSpec(section_type=PAGE_BREAK_SECTION),
            DocumentSectionSpec(section_type=SHORT_SOLUTIONS_SECTION),
        ))
    if content_config['include_full_solutions']:
        sections.extend((
            DocumentSectionSpec(section_type=PAGE_BREAK_SECTION),
            DocumentSectionSpec(section_type=FULL_SOLUTIONS_SECTION),
        ))

    return DocumentRecipe(
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
        sections=sections,
    )
