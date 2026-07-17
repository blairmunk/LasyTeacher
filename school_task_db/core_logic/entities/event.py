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
    work_type: str = ''
    work_type_display: str = ''
    variant_count: int = 0

    @property
    def pk(self) -> str:
        return self.id

    @property
    def variant_set(self):
        return self

    def count(self) -> int:
        return self.variant_count

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
class CourseSummary:
    pk: str
    name: str


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
    planned_date: Any = None
    location: str = ''
    description: str = ''
    short_uuid: str = ''
    work_type: str = ''
    work_type_display: str = ''
    work_variant_count: int = 0

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
        )

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
    event: Optional[EventEntity] = None
    participations: List[EventParticipationRow] = field(default_factory=list)
    some_variants_assigned: bool = False
    all_variants_assigned: bool = False
    can_review: bool = False
    status_color: str = 'secondary'
    status_steps: List[EventStatusStep] = field(default_factory=list)
    available_variants: List[EventVariantRef] = field(default_factory=list)
    status_transitions: List[EventStatusTransition] = field(default_factory=list)
