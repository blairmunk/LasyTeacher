"""Domain data for a written report about one completed event."""

from dataclasses import dataclass, field
from typing import Any, Tuple

from core_logic.value_objects.work_assessment import (
    WORK_ASSESSMENT_MODE_VARIANT,
    work_requires_variants,
)


@dataclass(frozen=True)
class EventReportEventRef:
    pk: str
    name: str
    status: str
    status_display: str
    planned_date: Any
    work_name: str
    course_name: str = ''
    work_assessment_mode: str = WORK_ASSESSMENT_MODE_VARIANT

    @property
    def has_task_level_results(self) -> bool:
        return work_requires_variants(self.work_assessment_mode)


@dataclass(frozen=True)
class EventReportCapturedEventFact:
    name: str
    planned_date: Any
    work_name: str
    work_assessment_mode: str = WORK_ASSESSMENT_MODE_VARIANT


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
    teacher_comment: str = ''
    needs_attention: bool = False


@dataclass(frozen=True)
class EventReportCapturedTaskFact:
    student_id: str
    student_name: str
    order: int
    topic_name: str
    subtopic_name: str = ''
    source_selection_id: str = ''
    content_order: int = 0
    is_assessable: bool = True
    points: float | None = None
    max_points: float | None = None
    comment: str = ''
    content_element: str = ''
    requirement_element: str = ''
    codifier_requirements: Tuple[str, ...] = field(default_factory=tuple)
    content_element_descriptions: Tuple[str, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(
            self,
            'codifier_requirements',
            tuple(self.codifier_requirements),
        )
        object.__setattr__(
            self,
            'content_element_descriptions',
            tuple(self.content_element_descriptions),
        )


@dataclass(frozen=True)
class EventReportTaskScoreFact:
    group_key: str
    order: int
    topic_name: str
    subtopic_name: str
    student_id: str
    student_name: str
    points: float | None
    max_points: float | None
    comment: str = ''


@dataclass(frozen=True)
class EventReportSpecificationFact:
    group_key: str
    order: int
    topic_name: str
    subtopic_name: str = ''
    content_element: str = ''
    requirement_element: str = ''
    codifier_requirements: Tuple[str, ...] = field(default_factory=tuple)
    content_element_descriptions: Tuple[str, ...] = field(
        default_factory=tuple,
    )


@dataclass(frozen=True)
class EventReportTaskFacts:
    task_scores: Tuple[EventReportTaskScoreFact, ...] = field(
        default_factory=tuple,
    )
    specification: Tuple[EventReportSpecificationFact, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'task_scores', tuple(self.task_scores))
        object.__setattr__(self, 'specification', tuple(self.specification))


@dataclass(frozen=True)
class EventPerformanceReportSource:
    event: EventReportEventRef
    participants: Tuple[EventReportParticipantFact, ...] = field(
        default_factory=tuple,
    )
    task_scores: Tuple[EventReportTaskScoreFact, ...] = field(
        default_factory=tuple,
    )
    specification: Tuple[EventReportSpecificationFact, ...] = field(
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
class EventReportSpecificationItem:
    order: int
    topics: Tuple[str, ...]
    subtopics: Tuple[str, ...]
    content_elements: Tuple[str, ...]
    content_element_descriptions: Tuple[str, ...]
    requirement_elements: Tuple[str, ...]


@dataclass(frozen=True)
class EventReportTeacherNote:
    student_name: str
    comment: str
    score: int | None = None
    needs_attention: bool = False


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
    specification_items: Tuple[EventReportSpecificationItem, ...]
    teacher_notes: Tuple[EventReportTeacherNote, ...]
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
