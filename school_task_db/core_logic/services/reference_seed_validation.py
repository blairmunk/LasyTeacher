"""Validate editable reference seed definitions."""

from core_logic.entities.reference_seed import (
    ReferenceSeedDefinition,
    ReferenceSeedValidationError,
)


def validate_reference_seed_definition(
    definition: ReferenceSeedDefinition,
) -> None:
    simple_keys = set()
    for item in definition.simple_references:
        if not item.category or not item.items_text.strip():
            raise ReferenceSeedValidationError(
                'Категория и элементы простого справочника обязательны.',
            )
        if item.category in simple_keys:
            raise ReferenceSeedValidationError(
                f'Повторяется простой справочник: {item.category}',
            )
        simple_keys.add(item.category)

    subject_keys = set()
    for item in definition.subject_references:
        key = (item.subject, item.grade_level, item.category)
        if not item.subject or not item.category or not item.items_text.strip():
            raise ReferenceSeedValidationError(
                'Предмет, категория и элементы справочника обязательны.',
            )
        if key in subject_keys:
            raise ReferenceSeedValidationError(
                'Повторяется предметный справочник: '
                f'{item.subject} {item.grade_level} {item.category}',
            )
        subject_keys.add(key)
