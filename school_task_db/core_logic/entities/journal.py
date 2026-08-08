"""DTOs for class journal reports."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report import (
    ReportCourseRef,
    ReportEventRef,
    ReportGroupRef,
    ReportMarkFact,
    ReportStudentRef,
    ReportVariantRef,
)


@dataclass(frozen=True)
class JournalParticipationRef:
    pk: str
    status: str


@dataclass(frozen=True)
class JournalEntryFact:
    student_id: str
    event_id: str
    participation: JournalParticipationRef | None = None
    mark: ReportMarkFact | None = None
    variant: ReportVariantRef | None = None


@dataclass(frozen=True)
class JournalSource:
    course: ReportCourseRef
    group: ReportGroupRef
    students: List[ReportStudentRef]
    events: List[ReportEventRef]
    entries: List[JournalEntryFact]
    courses: List[ReportCourseRef]


@dataclass(frozen=True)
class JournalSelectData:
    journal_links: List[dict]
    groups: Any
    courses: Any
    active_report: str = 'journal'
    active_course_pk: Any = None


@dataclass(frozen=True)
class JournalData:
    course: Any
    group: Any
    events: Any
    event_stats: List[dict]
    rows: List[dict]
    all_rows_count: int
    show_debts_only: bool
    total_debts: int
    students_with_debts: int
    courses: Any
    active_report: str = 'journal'
    active_course_pk: Any = None
