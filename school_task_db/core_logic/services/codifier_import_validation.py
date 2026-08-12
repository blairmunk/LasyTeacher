"""Validate codifier import definitions without persistence concerns."""

from core_logic.entities.codifier_import import (
    CodifierImportDefinition,
    CodifierImportValidationError,
)


def validate_codifier_import_definition(
    definition: CodifierImportDefinition,
) -> None:
    if not definition.name or not definition.short_name:
        raise CodifierImportValidationError(
            'Название и краткое название кодификатора обязательны.',
        )
    if not definition.subject or not definition.exam_type or not definition.year:
        raise CodifierImportValidationError(
            'Предмет, тип экзамена и год кодификатора обязательны.',
        )

    seen_content_codes = set()
    for item in definition.content:
        if item.code in seen_content_codes:
            raise CodifierImportValidationError(
                f'Повторяется код элемента содержания: {item.code}',
            )
        if item.parent_code and item.parent_code not in seen_content_codes:
            raise CodifierImportValidationError(
                f'Родитель {item.parent_code} для {item.code} '
                'должен быть объявлен раньше.',
            )
        seen_content_codes.add(item.code)

    requirement_codes = set()
    for item in definition.requirements:
        if item.code in requirement_codes:
            raise CodifierImportValidationError(
                f'Повторяется код требования: {item.code}',
            )
        requirement_codes.add(item.code)
