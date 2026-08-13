"""Student-related domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from core_logic.value_objects.task_scores import TaskScoreRecord


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
    variant_task_id: str = ''
    points: Optional[float] = None
    max_points: Optional[float] = None
    group_id: Optional[str] = None
    group_name: str = ''


@dataclass(frozen=True)
class TaskResultVariantRow:
    variant_task_id: str
    task_id: str


@dataclass(frozen=True)
class TaskResultGroupRef:
    task_id: str
    group_id: str
    group_name: str


@dataclass(frozen=True)
class TaskResultsSource:
    task_scores: tuple[TaskScoreRecord, ...] = field(default_factory=tuple)
    variant_tasks: tuple[TaskResultVariantRow, ...] = field(
        default_factory=tuple,
    )
    groups: tuple[TaskResultGroupRef, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, 'task_scores', tuple(self.task_scores))
        object.__setattr__(self, 'variant_tasks', tuple(self.variant_tasks))
        object.__setattr__(self, 'groups', tuple(self.groups))


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
class StudentTaskResultProfile:
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
    students: List["StudentListItem"]


@dataclass(frozen=True)
class StudentListItem:
    pk: str
    last_name: str
    first_name: str
    middle_name: str = ''
    email: str = ''
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class StudentDetail:
    pk: str
    first_name: str
    last_name: str
    middle_name: str = ''
    email: str = ''
    short_uuid: str = ''
    full_name: str = ''
    short_name: str = ''


@dataclass(frozen=True)
class StudentDetailData:
    student: Optional[StudentDetail] = None


@dataclass(frozen=True)
class SaveStudentParams:
    first_name: str
    last_name: str
    middle_name: str = ''
    email: str = ''
    student_id: str = ''


@dataclass(frozen=True)
class SaveStudentResult:
    status: str
    student_id: str = ''


@dataclass(frozen=True)
class StudentGroupListData:
    student_groups: List["StudentGroupListItem"]


@dataclass(frozen=True)
class StudentGroupListItem:
    pk: str
    name: str
    short_uuid: str
    created_at: datetime
    students_count: int = 0


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
class SaveStudentGroupParams:
    name: str
    student_ids: List[str] = field(default_factory=list)
    group_id: str = ''


@dataclass(frozen=True)
class SaveStudentGroupResult:
    status: str
    group_id: str = ''


@dataclass(frozen=True)
class StudentRemedialGroup:
    group: ObjectRef
    avg_pct: float
    total_done: int
    correct: int
    wrong: int
    available_count: int
    group_total: int
    available_tasks: tuple[ObjectRef, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(
            self,
            'available_tasks',
            tuple(self.available_tasks),
        )


@dataclass(frozen=True)
class StudentWeakTopic:
    topic: ObjectRef
    total: int
    correct: int
    avg_pct: float


@dataclass(frozen=True)
class StudentRemedialWorkData:
    no_data: bool = False
    remedial_groups: tuple[StudentRemedialGroup, ...] = field(
        default_factory=tuple,
    )
    weak_topics: tuple[StudentWeakTopic, ...] = field(default_factory=tuple)
    total_available: int = 0
    done_count: int = 0

    def __post_init__(self):
        object.__setattr__(
            self,
            'remedial_groups',
            tuple(self.remedial_groups),
        )
        object.__setattr__(self, 'weak_topics', tuple(self.weak_topics))


@dataclass(frozen=True)
class StudentRemedialTaskLog:
    task_id: str
    analog_group: Optional[ObjectRef] = None
    topic: Optional[ObjectRef] = None
    percentage: Optional[float] = None
    is_correct: Optional[bool] = None


@dataclass(frozen=True)
class StudentRemedialCandidateTask:
    task_id: str
    text: str
    analog_group_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(
            self,
            'analog_group_ids',
            tuple(self.analog_group_ids),
        )


@dataclass(frozen=True)
class StudentRemedialSource:
    task_logs: tuple[StudentRemedialTaskLog, ...] = field(
        default_factory=tuple,
    )
    tasks: tuple[StudentRemedialCandidateTask, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'task_logs', tuple(self.task_logs))
        object.__setattr__(self, 'tasks', tuple(self.tasks))


@dataclass(frozen=True)
class RemedialWizardTaskLog:
    student_id: str
    task_id: str
    analog_group_id: Optional[str] = None
    percentage: Optional[float] = None


@dataclass(frozen=True)
class RemedialWizardTask:
    task_id: str
    difficulty: int
    estimated_time: int = 0
    analog_group_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(
            self,
            'analog_group_ids',
            tuple(self.analog_group_ids),
        )


@dataclass(frozen=True)
class RemedialWizardAnalogGroup:
    group_id: str
    nominal_difficulty: int = 0


@dataclass(frozen=True)
class RemedialWizardPreviewSource:
    group: StudentGroupRef
    students: tuple[StudentDetail, ...] = field(default_factory=tuple)
    task_logs: tuple[RemedialWizardTaskLog, ...] = field(default_factory=tuple)
    tasks: tuple[RemedialWizardTask, ...] = field(default_factory=tuple)
    analog_groups: tuple[RemedialWizardAnalogGroup, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'students', tuple(self.students))
        object.__setattr__(self, 'task_logs', tuple(self.task_logs))
        object.__setattr__(self, 'tasks', tuple(self.tasks))
        object.__setattr__(self, 'analog_groups', tuple(self.analog_groups))


@dataclass(frozen=True)
class RemedialWizardPreviewItem:
    student: StudentDetail
    student_level: str
    overall_avg: float
    weak_groups: int
    tasks_count: int
    total_weight: int
    est_time: int
    available: bool
    reason: str = ''
    task_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, 'task_ids', tuple(self.task_ids))


@dataclass(frozen=True)
class RemedialWizardPreviewData:
    status: str = 'ready'
    group: Optional[StudentGroupRef] = None
    preview: tuple[RemedialWizardPreviewItem, ...] = field(
        default_factory=tuple,
    )
    threshold: int = 70
    limit_type: str = 'tasks'
    limit_value: int = 10
    work_name: str = 'Работа над ошибками'
    students_with_tasks: int = 0
    total_tasks: int = 0

    def __post_init__(self):
        object.__setattr__(self, 'preview', tuple(self.preview))
