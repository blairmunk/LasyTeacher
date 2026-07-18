"""Curriculum screen DTOs."""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CourseListData:
    courses: List["CourseListItem"] = field(default_factory=list)


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
class CourseDetailData:
    course: Optional["CourseDetailCourse"] = None
    assignments: List["CourseDetailAssignment"] = field(default_factory=list)
    total_variants: int = 0
    works_by_type: Dict[str, int] = field(default_factory=dict)
    groups_coverage: Dict[str, int] = field(default_factory=dict)


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
class TopicSubtopicsData:
    subtopics: List[dict] = field(default_factory=list)
