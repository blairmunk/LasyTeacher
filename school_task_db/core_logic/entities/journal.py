"""Read models and normalized facts for class journal reports."""

from dataclasses import dataclass, field
from typing import Optional

from core_logic.entities.report_refs import (
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
    participation: Optional[JournalParticipationRef] = None
    mark: Optional[ReportMarkFact] = None
    variant: Optional[ReportVariantRef] = None


@dataclass(frozen=True)
class JournalSource:
    course: ReportCourseRef
    group: ReportGroupRef
    students: tuple[ReportStudentRef, ...]
    events: tuple[ReportEventRef, ...]
    entries: tuple[JournalEntryFact, ...]
    courses: tuple[ReportCourseRef, ...]


@dataclass(frozen=True)
class JournalSelectLink:
    course: ReportCourseRef
    group: ReportGroupRef
    event_count: int


@dataclass(frozen=True)
class JournalSelectData:
    journal_links: tuple[JournalSelectLink, ...]
    groups: tuple[ReportGroupRef, ...]
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'journal'
    active_course_pk: Optional[str] = None


@dataclass(frozen=True)
class JournalCell:
    event: ReportEventRef
    participation: Optional[JournalParticipationRef]
    mark: Optional[ReportMarkFact]
    score: Optional[int]
    status: str
    css_class: str
    display: str
    variant: Optional[ReportVariantRef]


@dataclass(frozen=True)
class JournalRow:
    student: ReportStudentRef
    cells: tuple[JournalCell, ...]
    avg_score: Optional[float]
    score_count: int
    debts: int


@dataclass(frozen=True)
class JournalEventStat:
    event: ReportEventRef
    graded: int
    absent: int
    missing: int
    total: int


@dataclass(frozen=True)
class JournalData:
    course: ReportCourseRef
    group: ReportGroupRef
    events: tuple[ReportEventRef, ...]
    event_stats: tuple[JournalEventStat, ...]
    rows: tuple[JournalRow, ...]
    all_rows_count: int
    show_debts_only: bool
    total_debts: int
    students_with_debts: int
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'journal'
    active_course_pk: Optional[str] = None
