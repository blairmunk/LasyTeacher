"""Default section recipes for generated documents."""

from core_logic.entities.document import DocumentRecipe, DocumentSectionSpec
from core_logic.value_objects.content_config import (
    RemedialSheetBuildOptions,
    WorkDocumentBuildOptions,
)


WORK_DOCUMENT_TYPE = 'work'
REMEDIAL_SHEET_DOCUMENT_TYPE = 'remedial_sheet'

HEADER_SECTION = 'header'
TASK_VARIANTS_SECTION = 'task_variants'
ANSWERS_SECTION = 'answers'
SHORT_SOLUTIONS_SECTION = 'short_solutions'
FULL_SOLUTIONS_SECTION = 'full_solutions'
ORIGINAL_MISTAKES_SECTION = 'original_mistakes'
TRAINING_TASKS_SECTION = 'training_tasks'


def build_work_document_recipe(
    options: WorkDocumentBuildOptions | None = None,
) -> DocumentRecipe:
    options = options or WorkDocumentBuildOptions()
    content_config = options.content_config
    sections = [
        DocumentSectionSpec(section_type=HEADER_SECTION),
        DocumentSectionSpec(
            section_type=TASK_VARIANTS_SECTION,
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

    return DocumentRecipe(
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
        sections=sections,
    )
