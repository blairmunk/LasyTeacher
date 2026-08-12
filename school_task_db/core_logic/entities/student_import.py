"""Student CSV import entities."""

from dataclasses import dataclass, field
from datetime import date
from typing import Tuple


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


@dataclass(frozen=True)
class StudentImportAcademicYearRef:
    pk: str
    name: str
    is_active: bool = False


@dataclass(frozen=True)
class StudentImportGroupRef:
    pk: str
    name: str
    academic_year_name: str = ''


@dataclass(frozen=True)
class StudentImportStudentRef:
    pk: str
    last_name: str
    first_name: str
    middle_name: str = ''
    email: str = ''


@dataclass(frozen=True)
class StudentImportMembershipRef:
    group_id: str
    student_id: str


@dataclass(frozen=True)
class StudentImportSnapshot:
    academic_years: Tuple[StudentImportAcademicYearRef, ...] = ()
    groups: Tuple[StudentImportGroupRef, ...] = ()
    students: Tuple[StudentImportStudentRef, ...] = ()
    memberships: Tuple[StudentImportMembershipRef, ...] = ()


@dataclass(frozen=True)
class StudentImportAcademicYearCreate:
    name: str
    start_date: date
    end_date: date
    is_active: bool = False


@dataclass(frozen=True)
class StudentImportGroupCreate:
    token: str
    name: str
    academic_year_name: str = ''


@dataclass(frozen=True)
class StudentImportStudentMutation:
    token: str
    operation: str
    last_name: str
    first_name: str
    middle_name: str = ''
    email: str = ''


@dataclass(frozen=True)
class StudentImportMembershipCreate:
    group_token: str
    student_token: str


@dataclass(frozen=True)
class StudentImportStats:
    rows: int = 0
    years_created: int = 0
    groups_created: int = 0
    students_created: int = 0
    students_updated: int = 0
    memberships_created: int = 0


@dataclass(frozen=True)
class StudentImportPlan:
    academic_years_to_create: Tuple[
        StudentImportAcademicYearCreate,
        ...,
    ] = ()
    groups_to_create: Tuple[StudentImportGroupCreate, ...] = ()
    student_mutations: Tuple[StudentImportStudentMutation, ...] = ()
    memberships_to_create: Tuple[StudentImportMembershipCreate, ...] = ()
    stats: StudentImportStats = field(default_factory=StudentImportStats)


@dataclass(frozen=True)
class ImportStudentsRequest:
    rows: Tuple[StudentImportRow, ...]
    dry_run: bool = False


@dataclass(frozen=True)
class ImportStudentsResult:
    status: str
    dry_run: bool
    stats: StudentImportStats
