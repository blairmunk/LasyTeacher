"""Domain data for a written report about one completed event."""

from dataclasses import dataclass, field
from typing import Any, Tuple


@dataclass(frozen=True)
class EventReportEventRef:
    pk: str
    name: str
    status: str
    status_display: str
    planned_date: Any
    work_name: str
    course_name: str = ''


@dataclass(frozen=True)
class EventReportNarrative:
    possible_causes: str = ''
    recommendations: str = ''
    planned_actions: str = ''
    additional_notes: str = ''


@dataclass(frozen=True)
class EventReportParticipantFact:
    student_id: str
    student_name: str
    status: str
    score: int | None = None
    points: float | None = None
    max_points: float | None = None
    mistakes_analysis: str = ''
    recommendations: str = ''


@dataclass(frozen=True)
class EventReportTaskScoreFact:
    group_key: str
    order: int
    task_id: str
    task_text: str
    topic_name: str
    subtopic_name: str
    student_id: str
    student_name: str
    points: float | None
    max_points: float | None
    comment: str = ''


@dataclass(frozen=True)
class EventPerformanceReportSource:
    event: EventReportEventRef
    participants: Tuple[EventReportParticipantFact, ...] = field(
        default_factory=tuple,
    )
    task_scores: Tuple[EventReportTaskScoreFact, ...] = field(
        default_factory=tuple,
    )
    narrative: EventReportNarrative = field(
        default_factory=EventReportNarrative,
    )


@dataclass(frozen=True)
class EventReportTaskSummary:
    group_key: str
    order: int
    label: str
    topic_name: str
    subtopic_name: str
    attempts: int
    failed_count: int
    zero_count: int
    error_percentage: float
    average_percentage: float
    failed_students: Tuple[str, ...] = field(default_factory=tuple)
    comments: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EventReportTopicSummary:
    label: str
    attempts: int
    failed_count: int
    error_percentage: float
    average_percentage: float


@dataclass(frozen=True)
class EventPerformanceReportData:
    event: EventReportEventRef
    narrative: EventReportNarrative
    participants_total: int
    present_count: int
    absent_count: int
    graded_count: int
    average_score: float | None
    average_percentage: float | None
    pass_percentage: float
    quality_percentage: float
    grade_distribution: Tuple[tuple[int, int], ...]
    task_summaries: Tuple[EventReportTaskSummary, ...]
    weak_topics: Tuple[EventReportTopicSummary, ...]
    common_errors: Tuple[str, ...]
    suggested_causes: Tuple[str, ...]
    suggested_recommendations: Tuple[str, ...]
    suggested_actions: Tuple[str, ...]


@dataclass(frozen=True)
class SaveEventReportNarrativeParams:
    event_id: str
    narrative: EventReportNarrative


@dataclass(frozen=True)
class SaveEventReportNarrativeResult:
    status: str
    event_id: str = ''
