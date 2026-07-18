"""Task-related domain entities."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


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
    tasks: List["TaskListItem"]
    topics: Any
    analog_groups: Any
    sources: Any
    subtopics: Any
    task_types: List[Tuple[str, str]]
    difficulties: List[Tuple[int, str]]
    grade_choices: List[Tuple[int, str]]
    total_tasks: int
    ungrouped_count: int
    cache_stats: Any = None


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
    created_at: Any
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


@dataclass(frozen=True)
class TaskExportData:
    payload: Dict[str, Any]


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
    analog_groups: List["TaskGroupListItem"]
    topics: Any
    subtopics: Any
    difficulties: List[Tuple[int, str]]
    total_groups: int
    empty_groups: int
    total_tasks_in_groups: int


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
    tasks: List["TaskGroupDetailTask"] = None


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


@dataclass(frozen=True)
class AddTasksToGroupData:
    group: Any = None
    available_tasks: List["AddTasksToGroupTask"] = None
    search: str = ''
    status: str = 'ready'


@dataclass(frozen=True)
class AddTasksToGroupTask:
    pk: str
    topic: str
    text: str
    task_type_display: str
    difficulty_display: str
    section: str = ''
    created_at: Any = None
    image_count: int = 0


@dataclass(frozen=True)
class TaskDetailData:
    task: Optional["TaskDetailTask"] = None
    task_groups: List["TaskDetailGroup"] = None


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
    images: List[TaskDetailImage] = None
    created_at: Any = None


@dataclass(frozen=True)
class TaskDetailGroup:
    pk: str
    name: str


@dataclass(frozen=True)
class SelectOption:
    id: str
    name: str


@dataclass(frozen=True)
class ReferenceElementOption:
    code: str
    name: str


@dataclass(frozen=True)
class SourceListData:
    sources: List["SourceListItem"]


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
class MathCacheRefreshResult:
    status: str
    with_math_count: int = 0
    with_errors_count: int = 0
    with_warnings_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'refreshed'
