"""Student CSV import entities."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class StudentImportRow:
    row_number: int
    group_name: str
    academic_year_name: str
    last_name: str
    first_name: str
    middle_name: str = ''
    email: str = ''
    academic_year_start: date | None = None
    academic_year_end: date | None = None


class StudentImportValidationError(ValueError):
    """Raised when a student import row is invalid."""
