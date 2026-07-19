"""Adapters from generic document sections to legacy content config."""

from core_logic.entities.document import Document
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TASK_VARIANTS_SECTION,
)


def content_config_from_document(document: Document) -> dict:
    section_types = set(document.section_types)
    task_section = _first_section_payload(
        document,
        TASK_VARIANTS_SECTION,
        TASK_LIST_SECTION,
    )
    include_full_solutions = (
        FULL_SOLUTIONS_SECTION in section_types
        or bool(task_section.get('show_full_solutions', False))
    )
    include_short_solutions = (
        SHORT_SOLUTIONS_SECTION in section_types
        or bool(task_section.get('show_short_solutions', False))
        or include_full_solutions
    )
    include_answers = (
        ANSWERS_SECTION in section_types
        or ANSWER_KEY_SECTION in section_types
        or bool(task_section.get('show_answers', False))
        or include_short_solutions
        or include_full_solutions
    )

    return {
        'include_answers': include_answers,
        'include_short_solutions': include_short_solutions,
        'include_full_solutions': include_full_solutions,
        'answer_type': _answer_type(
            include_answers=include_answers,
            include_short_solutions=include_short_solutions,
            include_full_solutions=include_full_solutions,
        ),
        'include_hints': (
            task_section.get('include_hints')
            or task_section.get('show_hints')
            or False
        ),
        'include_instructions': (
            task_section.get('include_instructions')
            or task_section.get('show_instructions')
            or False
        ),
    }


def _first_section_payload(document: Document, *section_types: str) -> dict:
    for section in document.sections:
        if section.section_type in section_types:
            return dict(section.payload)
    return {}


def _answer_type(
    include_answers: bool,
    include_short_solutions: bool,
    include_full_solutions: bool,
) -> str:
    if include_full_solutions:
        return 'with_full_solutions'
    if include_short_solutions:
        return 'with_short_solutions'
    if include_answers:
        return 'with_answers'
    return 'tasks_only'
