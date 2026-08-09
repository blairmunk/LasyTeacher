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
class StudentDigestTaskResultFact:
    topic_name: str
    subtopic_name: str = ''
    subject: str = ''
    points: float | None = None
    max_points: float | None = None
    comment: str = ''
    is_assessable: bool = True

    @property
    def is_failed(self) -> bool:
        return bool(
            self.is_assessable
            and self.points is not None
            and self.max_points
            and self.points < self.max_points
        )

    @property
    def topic_label(self) -> str:
        if not self.topic_name:
            return self.subtopic_name
        if not self.subtopic_name:
            return self.topic_name
        return f'{self.topic_name}: {self.subtopic_name}'


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
    task_results: Tuple[StudentDigestTaskResultFact, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'task_results', tuple(self.task_results))

    @property
    def failed_topics(self) -> Tuple[str, ...]:
        return tuple(dict.fromkeys(
            result.topic_label
            for result in self.task_results
            if result.is_failed and result.topic_label
        ))

    @property
    def task_comments(self) -> Tuple[str, ...]:
        return tuple(dict.fromkeys(
            result.comment.strip()
            for result in self.task_results
            if result.is_failed and result.comment.strip()
        ))


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
