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
