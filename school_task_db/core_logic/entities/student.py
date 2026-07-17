"""Student-related domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional


class StudentLevel(Enum):
    WEAK = 'weak'
    MEDIUM = 'medium'
    STRONG = 'strong'

    @property
    def label_ru(self) -> str:
        return {
            self.WEAK: 'Слабый',
            self.MEDIUM: 'Средний',
            self.STRONG: 'Сильный',
        }[self]

    @property
    def color(self) -> str:
        return {
            self.WEAK: 'danger',
            self.MEDIUM: 'warning',
            self.STRONG: 'success',
        }[self]


@dataclass(frozen=True)
class TaskResult:
    """A student's result for one task."""

    task_id: str
    points: Optional[float] = None
    max_points: Optional[float] = None
    group_id: Optional[str] = None
    group_name: str = ''


@dataclass(frozen=True)
class ObjectRef:
    """Small template-friendly reference to a related object."""

    pk: str
    name: str = ''

    @property
    def text(self) -> str:
        return self.name


@dataclass(frozen=True)
class WorkRef:
    pk: str
    name: str
    work_type: str
    work_type_display: str

    def get_work_type_display(self) -> str:
        return self.work_type_display


@dataclass(frozen=True)
class EventRef:
    pk: str
    name: str
    planned_date: Optional[datetime] = None


@dataclass(frozen=True)
class MarkRef:
    pk: str
    score: Optional[int] = None
    points: Optional[float] = None
    max_points: Optional[float] = None
    teacher_comment: str = ''


@dataclass(frozen=True)
class StudentGroupRef:
    pk: str
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class StudentParticipationProfile:
    participation: ObjectRef
    event: EventRef
    work: Optional[WorkRef]
    mark: Optional[MarkRef]
    score: Optional[int]
    is_absent: bool
    variant_number: Optional[int] = None


@dataclass(frozen=True)
class StudentTaskLogProfile:
    task: ObjectRef
    event: Optional[ObjectRef]
    topic_name: str
    analog_group: Optional[ObjectRef]
    difficulty: Optional[int]
    points: Optional[float]
    max_points: Optional[float]
    is_correct: Optional[bool]
    percentage: Optional[float]
    completed_at: datetime


@dataclass(frozen=True)
class WorkGroupRef:
    work_id: str
    group_id: str
    group_name: str


@dataclass(frozen=True)
class StudentListData:
    students: Any


@dataclass(frozen=True)
class StudentDetailData:
    student: Any = None


@dataclass(frozen=True)
class StudentGroupListData:
    student_groups: Any


@dataclass(frozen=True)
class StudentGroupDetailData:
    student_group: Optional["StudentGroupDetail"] = None


@dataclass(frozen=True)
class StudentGroupDetailStudent:
    pk: str
    last_name: str
    first_name: str
    middle_name: str = ''
    email: str = ''
    short_uuid: str = ''


@dataclass(frozen=True)
class StudentGroupDetail:
    pk: str
    name: str
    short_uuid: str
    created_at: datetime
    students: List[StudentGroupDetailStudent] = field(default_factory=list)

    @property
    def students_count(self) -> int:
        return len(self.students)


@dataclass(frozen=True)
class StudentRemedialWorkData:
    no_data: bool = False
    remedial_groups: List[dict] = field(default_factory=list)
    weak_topics: Any = None
    total_available: int = 0
    done_count: int = 0


@dataclass(frozen=True)
class RemedialWizardPreviewData:
    status: str = 'ready'
    group: Any = None
    preview: List[dict] = field(default_factory=list)
    threshold: int = 70
    limit_type: str = 'tasks'
    limit_value: int = 10
    work_name: str = 'Работа над ошибками'
    students_with_tasks: int = 0
    total_tasks: int = 0
