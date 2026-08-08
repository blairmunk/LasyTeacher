"""Domain data for printable student grade digests."""

from dataclasses import dataclass, field
from datetime import date
from typing import Tuple

from core_logic.entities.academic_year import AcademicYearRef


@dataclass(frozen=True)
class StudentDigestGroupRef:
    pk: str
    name: str


@dataclass(frozen=True)
class StudentDigestStudentRef:
    pk: str
    full_name: str


@dataclass(frozen=True)
class StudentDigestEntryFact:
    event_id: str
    event_name: str
    work_name: str
    subject: str
    planned_date: date
    status: str
    score: int | None = None
    points: float | None = None
    max_points: float | None = None
    teacher_comment: str = ''
    mistakes_analysis: str = ''
    recommendations: str = ''
    needs_attention: bool = False
    failed_topics: Tuple[str, ...] = field(default_factory=tuple)
    task_comments: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class StudentDigestStudentSource:
    student: StudentDigestStudentRef
    entries: Tuple[StudentDigestEntryFact, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class StudentDigestSource:
    group: StudentDigestGroupRef
    students: Tuple[StudentDigestStudentSource, ...] = field(
        default_factory=tuple,
    )


@dataclass(frozen=True)
class StudentDigestOptions:
    include_summary: bool = True
    include_details: bool = True
    include_focus: bool = True
    include_retakes: bool = True
    include_teacher_comments: bool = False
    include_task_comments: bool = False
    include_absences: bool = True
    retake_score_threshold: int = 2


@dataclass(frozen=True)
class StudentDigestEntry:
    event_id: str
    event_name: str
    work_name: str
    planned_date: date
    status: str
    score: int | None
    points: float | None
    max_points: float | None
    focus: str
    focus_items: Tuple[str, ...]
    teacher_comment: str
    needs_retake: bool
    retake_reason: str


@dataclass(frozen=True)
class StudentDigestSubject:
    title: str
    entries: Tuple[StudentDigestEntry, ...]
    average_score: float | None


@dataclass(frozen=True)
class StudentDigestData:
    student: StudentDigestStudentRef
    group_name: str
    subjects: Tuple[StudentDigestSubject, ...]
    average_score: float | None
    grades_count: int
    absent_count: int
    retake_entries: Tuple[StudentDigestEntry, ...]
    focus_items: Tuple[str, ...]
    teacher_comment_entries: Tuple[StudentDigestEntry, ...]


@dataclass(frozen=True)
class StudentDigestPageData:
    groups: Tuple[StudentDigestGroupRef, ...]
    selected_group: StudentDigestGroupRef | None
    start_date: date
    end_date: date
    options: StudentDigestOptions
    students: Tuple[StudentDigestStudentRef, ...] = field(default_factory=tuple)
    selected_student: StudentDigestStudentRef | None = None
    digests: Tuple[StudentDigestData, ...] = field(default_factory=tuple)
    active_report: str = 'student-digests'


@dataclass(frozen=True)
class StudentDigestRequest:
    group_id: str = ''
    student_id: str = ''
    start_date: date | None = None
    end_date: date | None = None
    year: AcademicYearRef | None = None
    options: StudentDigestOptions = field(default_factory=StudentDigestOptions)
