"""Event-related domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, NamedTuple, Optional

from core_logic.value_objects.task_scores import TaskScoreRecord
from core_logic.value_objects.work_assessment import (
    WORK_ASSESSMENT_MODE_VARIANT,
    work_requires_variants,
)


def _same_pk(left_id: str, other: Any) -> bool:
    other_id = getattr(other, 'pk', getattr(other, 'id', None))
    return other_id is not None and str(left_id) == str(other_id)


@dataclass(frozen=True)
class WorkSummary:
    id: str
    name: str
    work_type: str = ''
    work_type_display: str = ''
    variant_count: int = 0
    assessment_mode: str = WORK_ASSESSMENT_MODE_VARIANT

    @property
    def pk(self) -> str:
        return self.id

    @property
    def variant_set(self):
        return self

    def count(self) -> int:
        return self.variant_count

    @property
    def requires_variants(self) -> bool:
        return work_requires_variants(self.assessment_mode)

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class VariantSummary:
    id: str
    number: int

    @property
    def pk(self) -> str:
        return self.id

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class StudentSummary:
    id: str
    full_name: str
    short_name: str = ''

    @property
    def pk(self) -> str:
        return self.id

    def get_full_name(self) -> str:
        return self.full_name

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class CourseSummary:
    pk: str
    name: str


@dataclass(frozen=True)
class EventListItem:
    pk: str
    name: str
    status: str
    status_display: str
    planned_date: Optional[datetime] = None
    participant_count: int = 0
    work: Optional[WorkSummary] = None
    course: Optional[CourseSummary] = None


@dataclass(frozen=True)
class EventEntity:
    id: str
    name: str
    work_id: str
    work_name: str
    status: str = ''
    status_display: str = ''
    course_id: Optional[str] = None
    course_name: str = ''
    planned_date: Optional[datetime] = None
    location: str = ''
    description: str = ''
    short_uuid: str = ''
    work_type: str = ''
    work_type_display: str = ''
    work_variant_count: int = 0
    participant_group_names: str = ''
    work_assessment_mode: str = WORK_ASSESSMENT_MODE_VARIANT

    @property
    def pk(self) -> str:
        return self.id

    @property
    def work(self):
        return WorkSummary(
            id=self.work_id,
            name=self.work_name,
            work_type=self.work_type,
            work_type_display=self.work_type_display,
            variant_count=self.work_variant_count,
            assessment_mode=self.work_assessment_mode,
        )

    @property
    def requires_variants(self) -> bool:
        return work_requires_variants(self.work_assessment_mode)

    @property
    def course(self):
        if not self.course_id:
            return None
        return CourseSummary(pk=self.course_id, name=self.course_name)

    @property
    def date(self):
        return self.planned_date

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class EventParticipationRef:
    id: str
    event_id: str

    @property
    def pk(self) -> str:
        return self.id

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class ParticipationGradingContext:
    event_status: str
    other_active_participants: int
    other_graded_participants: int


@dataclass(frozen=True)
class CheckedAttemptRef:
    student_id: str
    event_id: str
    score: Optional[int] = None
    participation_id: str = ''
    attempt_snapshot_id: str = ''


@dataclass(frozen=True)
class ParticipationAttemptData:
    student: StudentSummary
    variant: Optional[VariantSummary]
    score: Optional[int] = None
    points: Optional[float] = None
    max_points: Optional[float] = None
    task_scores: tuple[TaskScoreRecord, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, 'task_scores', tuple(self.task_scores))


@dataclass(frozen=True)
class EventStatusStep:
    code: str
    label: str
    color: str
    current: bool
    passed: bool


class EventStatusTransition(NamedTuple):
    new_status: str
    label: str
    color: str
    icon: str


@dataclass(frozen=True)
class EventListData:
    events: tuple[EventListItem, ...] = field(default_factory=tuple)
    planned_events: tuple[EventListItem, ...] = field(default_factory=tuple)
    active_events: tuple[EventListItem, ...] = field(default_factory=tuple)
    graded_events: tuple[EventListItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EventStudentRef:
    pk: str
    last_name: str
    first_name: str
    middle_name: str = ''


@dataclass(frozen=True)
class EventVariantRef:
    pk: str
    number: int


@dataclass(frozen=True)
class EventWorkScanRef:
    url: str


@dataclass(frozen=True)
class EventMarkRef:
    score: Optional[int] = None
    work_scan: Optional[EventWorkScanRef] = None


@dataclass(frozen=True)
class EventVariantAssignmentResult:
    variant_number: int
    student_last_name: str
    student_first_name: str

    @property
    def student_name(self) -> str:
        return f'{self.student_last_name} {self.student_first_name}'.strip()


@dataclass(frozen=True)
class EventParticipationRow:
    pk: str
    status: str
    student: EventStudentRef
    variant: Optional[EventVariantRef] = None
    mark_obj: Optional[EventMarkRef] = None


@dataclass(frozen=True)
class EventDetailData:
    event: Optional[EventEntity] = None
    participations: tuple[EventParticipationRow, ...] = field(
        default_factory=tuple,
    )
    some_variants_assigned: bool = False
    all_variants_assigned: bool = False
    variants_required: bool = True
    can_review: bool = False
    status_color: str = 'secondary'
    status_steps: tuple[EventStatusStep, ...] = field(default_factory=tuple)
    available_variants: tuple[EventVariantRef, ...] = field(
        default_factory=tuple,
    )
    status_transitions: tuple[EventStatusTransition, ...] = field(
        default_factory=tuple,
    )
