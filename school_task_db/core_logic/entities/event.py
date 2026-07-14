"""Event-related domain entities."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, NamedTuple, Optional


def _same_pk(left_id: str, other: Any) -> bool:
    other_id = getattr(other, 'pk', getattr(other, 'id', None))
    return other_id is not None and str(left_id) == str(other_id)


@dataclass(frozen=True)
class WorkSummary:
    id: str
    name: str

    @property
    def pk(self) -> str:
        return self.id

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

    @property
    def pk(self) -> str:
        return self.id

    def get_full_name(self) -> str:
        return self.full_name

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class EventEntity:
    id: str
    name: str
    work_id: str
    work_name: str
    course_id: Optional[str] = None

    @property
    def pk(self) -> str:
        return self.id

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class MarkEntity:
    student_id: str
    event_id: str
    score: Optional[int] = None


@dataclass(frozen=True)
class ParticipationMarkData:
    student: StudentSummary
    variant: Optional[VariantSummary]
    score: Optional[int] = None
    points: Optional[float] = None
    max_points: Optional[float] = None
    task_scores: Dict[str, dict] = None


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
    events: List[Any] = field(default_factory=list)
    planned_events: List[Any] = field(default_factory=list)
    active_events: List[Any] = field(default_factory=list)
    graded_events: List[Any] = field(default_factory=list)


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
    participations: List[EventParticipationRow]
    some_variants_assigned: bool
    all_variants_assigned: bool
    can_review: bool
    status_color: str
    status_steps: List[EventStatusStep]
    available_variants: List[EventVariantRef]
    status_transitions: List[EventStatusTransition]
