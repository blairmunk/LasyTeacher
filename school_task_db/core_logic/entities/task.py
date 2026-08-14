"""Task-related domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_LABELS,
)


@dataclass(frozen=True)
class TaskEntity:
    id: str
    text: str = ''
    difficulty: int = 1
    estimated_time: Optional[int] = None


@dataclass(frozen=True)
class TaskListFilters:
    search: str = ''
    topic_id: str = ''
    subtopic_id: str = ''
    task_type: str = ''
    difficulty: str = ''
    group_filter: str = ''
    analog_group_id: str = ''
    math_filter: str = 'all'
    source_id: str = ''
    grade: str = ''
    verified: str = ''


@dataclass(frozen=True)
class TaskListData:
    tasks: tuple["TaskListItem", ...]
    topics: tuple["SelectOption", ...]
    analog_groups: tuple["SelectOption", ...]
    sources: tuple["SelectOption", ...]
    subtopics: tuple["SelectOption", ...]
    task_types: tuple[Tuple[str, str], ...]
    difficulties: tuple[Tuple[int, str], ...]
    grade_choices: tuple[Tuple[int, str], ...]
    total_tasks: int
    ungrouped_count: int
    cache_stats: Any = None

    def __post_init__(self):
        for field_name in (
            'tasks',
            'topics',
            'analog_groups',
            'sources',
            'subtopics',
            'task_types',
            'difficulties',
            'grade_choices',
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))


@dataclass(frozen=True)
class TaskListSourceRef:
    pk: str
    name: str
    short_name: str = ''

    def __str__(self) -> str:
        return self.short_name or self.name


@dataclass(frozen=True)
class TaskListSubtopicRef:
    pk: str
    name: str


@dataclass(frozen=True)
class TaskListItem:
    pk: str
    text: str
    topic_name: str
    task_type_display: str
    difficulty_display: str
    display_id: str
    created_at: datetime
    subtopic: Optional[TaskListSubtopicRef] = None
    source: Optional[TaskListSourceRef] = None
    grade: Optional[int] = None
    is_verified: bool = False
    has_group: bool = False
    group_count: int = 0
    image_count: int = 0


@dataclass(frozen=True)
class TaskExportFilters:
    topic_id: str = ''
    subject: str = ''
    grade: str = ''
    limit: int | None = None


@dataclass(frozen=True)
class TaskExportData:
    payload: Dict[str, Any]


@dataclass(frozen=True)
class TaskExportTopicRef:
    name: str
    subject: str
    grade_level: int
    section: str = ''
    description: str = ''


@dataclass(frozen=True)
class TaskExportSourceRef:
    pk: str
    name: str
    short_name: str = ''
    source_type: str = ''
    author: str = ''
    year: Any = None
    url: str = ''
    isbn: str = ''


@dataclass(frozen=True)
class TaskExportGroupRef:
    pk: str
    name: str
    description: str = ''
    difficulty: int = 0
    bank_role: str = TASK_BANK_ROLE_CONTROL


@dataclass(frozen=True)
class TaskExportClassificationRef:
    subject: str
    exam_type: str
    year: int
    code: str
    name: str = ''
    codifier_name: str = ''


@dataclass(frozen=True)
class TaskExportImageSource:
    pk: str
    task_id: str
    filename: str
    position: str
    caption: str
    order: int
    base64_data: str


@dataclass(frozen=True)
class TaskExportTaskSource:
    pk: str
    text: str
    answer: str = ''
    short_solution: str = ''
    full_solution: str = ''
    hint: str = ''
    instruction: str = ''
    difficulty: int = 0
    task_type: str = ''
    cognitive_level: str = ''
    estimated_time: Any = None
    grade: Any = None
    year: Any = None
    is_verified: bool = False
    teacher_notes: str = ''
    source_detail: str = ''
    topic: Optional[TaskExportTopicRef] = None
    source: Optional[TaskExportSourceRef] = None
    groups: tuple[TaskExportGroupRef, ...] = field(default_factory=tuple)
    images: tuple[TaskExportImageSource, ...] = field(default_factory=tuple)
    content_entries: tuple[TaskExportClassificationRef, ...] = field(
        default_factory=tuple,
    )
    requirements: tuple[TaskExportClassificationRef, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'groups', tuple(self.groups))
        object.__setattr__(self, 'images', tuple(self.images))
        object.__setattr__(self, 'content_entries', tuple(self.content_entries))
        object.__setattr__(self, 'requirements', tuple(self.requirements))


@dataclass(frozen=True)
class TaskGroupListFilters:
    search: str = ''
    topic_id: str = ''
    subtopic_id: str = ''
    difficulty: str = ''
    group_filter: str = ''
    sort: str = 'name'
    min_tasks: str = ''
    max_tasks: str = ''


@dataclass(frozen=True)
class TaskGroupListData:
    analog_groups: tuple["TaskGroupListItem", ...]
    topics: tuple["SelectOption", ...]
    subtopics: tuple["SelectOption", ...]
    difficulties: tuple[Tuple[int, str], ...]
    total_groups: int
    empty_groups: int
    total_tasks_in_groups: int

    def __post_init__(self):
        for field_name in (
            'analog_groups',
            'topics',
            'subtopics',
            'difficulties',
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))


@dataclass(frozen=True)
class TaskGroupListItem:
    pk: str
    name: str
    description: str = ''
    task_count: int = 0
    avg_difficulty: Optional[float] = None
    sample_task_text: str = ''


@dataclass(frozen=True)
class TaskGroupDetailData:
    group: Optional["TaskGroupDetailGroup"] = None
    tasks: tuple["TaskGroupDetailTask", ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, 'tasks', tuple(self.tasks))


@dataclass(frozen=True)
class TaskGroupDetailGroup:
    pk: str
    name: str
    description: str = ''


@dataclass(frozen=True)
class TaskGroupDetailTask:
    pk: str
    topic: str
    text: str
    task_type_display: str
    difficulty_display: str
    image_count: int = 0
    bank_role: str = TASK_BANK_ROLE_CONTROL

    @property
    def bank_role_label(self) -> str:
        return TASK_BANK_ROLE_LABELS.get(self.bank_role, self.bank_role)


@dataclass(frozen=True)
class AddTasksToGroupData:
    group: Optional[TaskGroupDetailGroup] = None
    available_tasks: tuple["AddTasksToGroupTask", ...] = field(
        default_factory=tuple,
    )
    search: str = ''
    status: str = 'ready'

    def __post_init__(self):
        object.__setattr__(self, 'available_tasks', tuple(self.available_tasks))


@dataclass(frozen=True)
class AddTasksToGroupTask:
    pk: str
    topic: str
    text: str
    task_type_display: str
    difficulty_display: str
    section: str = ''
    created_at: Optional[datetime] = None
    image_count: int = 0


@dataclass(frozen=True)
class TaskDetailData:
    task: Optional["TaskDetailTask"] = None
    task_groups: tuple["TaskDetailGroup", ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, 'task_groups', tuple(self.task_groups))


@dataclass(frozen=True)
class TaskDetailSource:
    name: str
    url: str = ''

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class TaskDetailImage:
    caption: str = ''
    position: str = ''
    safe_url: Optional[str] = None
    image_name: str = ''
    css_class: str = 'task-image-bottom-70'


@dataclass(frozen=True)
class TaskDetailClassification:
    codifier_name: str
    code: str
    name: str


@dataclass(frozen=True)
class TaskDetailTask:
    pk: str
    topic: str
    section: str
    text: str
    answer: str
    task_type_display: str
    difficulty_display: str
    short_uuid: str
    subtopic: str = ''
    short_solution: str = ''
    full_solution: str = ''
    hint: str = ''
    instruction: str = ''
    source: Optional[TaskDetailSource] = None
    source_detail: str = ''
    grade: Optional[int] = None
    year: Optional[int] = None
    is_verified: bool = False
    estimated_time: Optional[int] = None
    teacher_notes: str = ''
    images: tuple[TaskDetailImage, ...] = field(default_factory=tuple)
    created_at: Optional[datetime] = None
    content_entries: Tuple[TaskDetailClassification, ...] = ()
    requirements: Tuple[TaskDetailClassification, ...] = ()
    legacy_content_element: str = ''
    legacy_requirement_element: str = ''

    def __post_init__(self):
        object.__setattr__(self, 'images', tuple(self.images))
        object.__setattr__(self, 'content_entries', tuple(self.content_entries))
        object.__setattr__(self, 'requirements', tuple(self.requirements))


@dataclass(frozen=True)
class TaskDetailGroup:
    pk: str
    name: str


@dataclass(frozen=True)
class TaskSaveParams:
    text: str
    answer: str
    topic_id: str
    task_type: str
    difficulty: int
    task_id: str = ''
    subtopic_id: Optional[str] = None
    cognitive_level: str = 'understand'
    content_entry_ids: Tuple[str, ...] = ()
    requirement_ids: Tuple[str, ...] = ()
    short_solution: str = ''
    full_solution: str = ''
    hint: str = ''
    instruction: str = ''
    estimated_time: Optional[int] = None
    source_id: Optional[str] = None
    source_detail: str = ''
    grade: Optional[int] = None
    year: Optional[int] = None
    is_verified: bool = False
    teacher_notes: str = ''

    def __post_init__(self):
        object.__setattr__(self, 'content_entry_ids', tuple(dict.fromkeys(
            self.content_entry_ids,
        )))
        object.__setattr__(self, 'requirement_ids', tuple(dict.fromkeys(
            self.requirement_ids,
        )))


@dataclass(frozen=True)
class TaskSaveResult:
    status: str
    task_id: str = ''
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskImageSaveParams:
    image_id: str = ''
    image: Any = None
    position: str = ''
    caption: str = ''
    order: int = 1
    delete: bool = False


@dataclass(frozen=True)
class TaskImagesSaveResult:
    status: str
    created_images: int = 0
    deleted_images: int = 0


@dataclass(frozen=True)
class SelectOption:
    id: str
    name: str

    @property
    def pk(self) -> str:
        return self.id

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class TaskClassificationOptions:
    content_entries: tuple[SelectOption, ...]
    requirements: tuple[SelectOption, ...]

    def __post_init__(self):
        object.__setattr__(self, 'content_entries', tuple(self.content_entries))
        object.__setattr__(self, 'requirements', tuple(self.requirements))


@dataclass(frozen=True)
class SourceListData:
    sources: tuple["SourceListItem", ...]

    def __post_init__(self):
        object.__setattr__(self, 'sources', tuple(self.sources))


@dataclass(frozen=True)
class SourceListItem:
    pk: str
    name: str
    source_type_display: str
    short_name: str = ''
    author: str = ''
    year: Optional[int] = None
    url: str = ''
    task_count: int = 0


@dataclass(frozen=True)
class SourceCreateParams:
    name: str
    short_name: str = ''
    source_type: str = 'textbook'
    author: str = ''
    year: Optional[int] = None
    url: str = ''
    isbn: str = ''
    notes: str = ''


@dataclass(frozen=True)
class SourceCreateResult:
    pk: str
    display_name: str


@dataclass(frozen=True)
class MathCacheRefreshResult:
    status: str
    with_math_count: int = 0
    with_errors_count: int = 0
    with_warnings_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'refreshed'
