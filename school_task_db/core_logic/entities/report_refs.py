"""Shared immutable references used by report DTOs."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReportStudentRef:
    pk: str
    full_name: str
    short_name: str = ''
    last_name: str = ''
    first_name: str = ''


@dataclass(frozen=True)
class ReportCourseRef:
    pk: str
    name: str


@dataclass(frozen=True)
class ReportGroupRef:
    pk: str
    name: str
    students_count: int = 0


@dataclass(frozen=True)
class ReportTaskRef:
    pk: str
    text: str
    difficulty: int
    difficulty_display: str


@dataclass(frozen=True)
class ReportActivityRef:
    pk: str
    name: str
    planned_date: Any = None


@dataclass(frozen=True)
class ReportTaskUsageRef:
    pk: str
    short_uuid: str
    text: str
    variant_count: int


@dataclass(frozen=True)
class ReportVariantRef:
    pk: str
    short_uuid: str
    number: int
    work_name_snapshot: str


@dataclass(frozen=True)
class ReportAnalogGroupRef:
    pk: str
    name: str


@dataclass(frozen=True)
class ReportWorkRef:
    pk: str
    name: str
    work_type: str
    work_type_display: str
    duration: int
    variant_count: int = 0


@dataclass(frozen=True)
class ReportMarkFact:
    score: int | None
    points: float | None
    max_points: float | None


@dataclass(frozen=True)
class ReportEventRef:
    pk: str
    name: str
    status: str
    status_display: str
    planned_date: Any
    actual_end: Any = None
    location: str = ''
    work: Any = None
    participants_count: int = 0
    graded_count: int = 0
    progress_percentage: int = 0
