"""Factories for default document recipes."""

from core_logic.entities.document import DocumentRecipe, DocumentSectionSpec
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    EVENT_REPORT_CONCLUSIONS_SECTION,
    EVENT_REPORT_SUMMARY_SECTION,
    EVENT_REPORT_SPECIFICATION_SECTION,
    EVENT_REPORT_TASK_ANALYSIS_SECTION,
    EVENT_REPORT_TEACHER_NOTES_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    PAGE_BREAK_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    STUDENT_DIGEST_DETAILS_SECTION,
    STUDENT_DIGEST_DOCUMENT_TYPE,
    STUDENT_DIGEST_FOCUS_SECTION,
    STUDENT_DIGEST_RETAKES_SECTION,
    STUDENT_DIGEST_SUMMARY_SECTION,
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


def build_event_performance_report_document_recipe(
    include_content_element_text: bool = True,
    include_teacher_notes: bool = False,
) -> DocumentRecipe:
    sections = [
        DocumentSectionSpec(section_type=HEADER_SECTION),
        DocumentSectionSpec(
            section_type=EVENT_REPORT_SPECIFICATION_SECTION,
            options={
                'include_content_element_text': (
                    include_content_element_text
                ),
            },
        ),
        DocumentSectionSpec(section_type=EVENT_REPORT_SUMMARY_SECTION),
        DocumentSectionSpec(
            section_type=EVENT_REPORT_TASK_ANALYSIS_SECTION,
        ),
        DocumentSectionSpec(
            section_type=EVENT_REPORT_CONCLUSIONS_SECTION,
        ),
    ]
    if include_teacher_notes:
        sections.append(
            DocumentSectionSpec(
                section_type=EVENT_REPORT_TEACHER_NOTES_SECTION,
            )
        )
    return DocumentRecipe(
        document_type=EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
        sections=sections,
    )


def build_student_digest_document_recipe(options) -> DocumentRecipe:
    sections = [DocumentSectionSpec(section_type=HEADER_SECTION)]
    if options.include_summary:
        sections.append(
            DocumentSectionSpec(section_type=STUDENT_DIGEST_SUMMARY_SECTION),
        )
    if options.include_retakes:
        sections.append(
            DocumentSectionSpec(section_type=STUDENT_DIGEST_RETAKES_SECTION),
        )
    if options.include_details:
        sections.append(
            DocumentSectionSpec(section_type=STUDENT_DIGEST_DETAILS_SECTION),
        )
    if options.include_focus:
        sections.append(
            DocumentSectionSpec(section_type=STUDENT_DIGEST_FOCUS_SECTION),
        )
    return DocumentRecipe(
        document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
        sections=sections,
    )
