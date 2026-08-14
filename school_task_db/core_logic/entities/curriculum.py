"""Curriculum screen DTOs."""

from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType
from typing import Mapping, Optional


@dataclass(frozen=True)
class CourseListData:
    courses: tuple['CourseListItem', ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CourseListItem:
    pk: str
    name: str
    subject: str
    grade_level: int
    academic_year: str = ''
    is_active: bool = False
    description: str = ''
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours_per_week: Optional[int] = None
    assignments_count: int = 0


@dataclass(frozen=True)
class TopicListData:
    topics: tuple['TopicListItem', ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TopicListItem:
    pk: str
    name: str
    subject: str
    section: str
    grade_level: int
    order: int
    difficulty_level: int
    difficulty_level_display: str
    description: str = ''
    subtopics_count: int = 0


@dataclass(frozen=True)
class TopicDetailData:
    topic: Optional["TopicDetailTopic"] = None
    subtopics: tuple['TopicDetailSubtopic', ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TopicDetailTopic:
    pk: str
    name: str
    subject: str
    section: str
    grade_level: int
    order: int
    difficulty_level: int
    difficulty_level_display: str
    description: str = ''


@dataclass(frozen=True)
class TopicDetailSubtopic:
    pk: str
    name: str
    description: str = ''
    order: int = 0


@dataclass(frozen=True)
class CourseDetailData:
    course: Optional["CourseDetailCourse"] = None
    assignments: tuple['CourseDetailAssignment', ...] = field(default_factory=tuple)
    total_variants: int = 0
    works_by_type: Mapping[str, int] = field(default_factory=dict)
    groups_coverage: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, 'assignments', tuple(self.assignments))
        object.__setattr__(
            self,
            'works_by_type',
            MappingProxyType(dict(self.works_by_type)),
        )
        object.__setattr__(
            self,
            'groups_coverage',
            MappingProxyType(dict(self.groups_coverage)),
        )


@dataclass(frozen=True)
class CourseDetailCourse:
    pk: str
    name: str
    subject: str
    grade_level: int
    academic_year: str = ''
    is_active: bool = False
    description: str = ''
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours_per_week: Optional[int] = None
    total_hours: Optional[int] = None


@dataclass(frozen=True)
class CourseDetailWork:
    pk: str
    name: str
    work_type: str
    work_type_display: str


@dataclass(frozen=True)
class CourseDetailAssignment:
    order: int
    work: CourseDetailWork
    weight: float
    planned_date: Optional[date] = None
    groups_count: int = 0
    tasks_per_variant: int = 0
    variants_count: int = 0


@dataclass(frozen=True)
class CourseDetailWorkGroup:
    group_name: str
    count: int = 0


@dataclass(frozen=True)
class TopicSubtopicOption:
    id: str
    name: str
    description: str = ''


@dataclass(frozen=True)
class TopicSubtopicsData:
    subtopics: tuple[TopicSubtopicOption, ...] = field(default_factory=tuple)
