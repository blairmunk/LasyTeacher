"""Task-related domain entities."""

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


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
    tasks: Any
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
    analog_groups: Any
    topics: Any
    subtopics: Any
    difficulties: List[Tuple[int, str]]
    total_groups: int
    empty_groups: int
    total_tasks_in_groups: int


@dataclass(frozen=True)
class TaskDetailData:
    task_groups: Any


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
    sources: Any


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
