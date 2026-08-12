"""Parse and validate normalized student CSV rows."""

from datetime import date
from typing import Iterable, Mapping, Tuple

from core_logic.entities.student_import import (
    StudentImportRow,
    StudentImportValidationError,
)


CLASS_COLUMNS = ('class', 'group', 'student_group', 'класс', 'группа')
YEAR_COLUMNS = ('academic_year', 'year', 'учебный_год', 'год')
LAST_NAME_COLUMNS = ('last_name', 'lastname', 'фамилия')
FIRST_NAME_COLUMNS = ('first_name', 'firstname', 'имя')
MIDDLE_NAME_COLUMNS = ('middle_name', 'middlename', 'отчество')
EMAIL_COLUMNS = ('email', 'почта')


def parse_student_csv_rows(
    rows: Iterable[Mapping[str, str | None]],
    first_row_number: int = 2,
) -> Tuple[StudentImportRow, ...]:
    return tuple(
        _parse_row(row, row_number)
        for row_number, row in enumerate(rows, start=first_row_number)
    )


def _parse_row(
    row: Mapping[str, str | None],
    row_number: int,
) -> StudentImportRow:
    group_name = _row_value(row, CLASS_COLUMNS)
    academic_year_name = _row_value(row, YEAR_COLUMNS)
    last_name = _row_value(row, LAST_NAME_COLUMNS)
    first_name = _row_value(row, FIRST_NAME_COLUMNS)

    if not group_name:
        raise StudentImportValidationError(
            f'Строка {row_number}: класс обязателен.',
        )
    if not last_name:
        raise StudentImportValidationError(
            f'Строка {row_number}: фамилия обязательна.',
        )
    if not first_name:
        raise StudentImportValidationError(
            f'Строка {row_number}: имя обязательно.',
        )

    year_start = None
    year_end = None
    if academic_year_name:
        year_start, year_end = parse_academic_year(academic_year_name)

    return StudentImportRow(
        row_number=row_number,
        group_name=group_name,
        academic_year_name=academic_year_name,
        last_name=last_name,
        first_name=first_name,
        middle_name=_row_value(row, MIDDLE_NAME_COLUMNS),
        email=_row_value(row, EMAIL_COLUMNS),
        academic_year_start=year_start,
        academic_year_end=year_end,
    )


def parse_academic_year(name: str) -> tuple[date, date]:
    normalized = name.replace('–', '-').replace('—', '-')
    parts = normalized.split('-')
    if len(parts) != 2:
        raise _academic_year_format_error(name)
    try:
        start_year = int(parts[0])
        end_year = int(parts[1])
    except ValueError as error:
        raise _academic_year_format_error(name) from error
    if end_year != start_year + 1:
        raise StudentImportValidationError(
            f'Учебный год должен покрывать два соседних года: {name}',
        )
    return date(start_year, 9, 1), date(end_year, 8, 31)


def _row_value(
    row: Mapping[str, str | None],
    aliases: tuple[str, ...],
) -> str:
    for alias in aliases:
        value = row.get(alias)
        if value is not None:
            return value.strip()
    return ''


def _academic_year_format_error(name: str) -> StudentImportValidationError:
    return StudentImportValidationError(
        f'Учебный год должен быть в формате 2026-2027: {name}',
    )
