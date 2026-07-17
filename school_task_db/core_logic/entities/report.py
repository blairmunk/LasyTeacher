"""Report DTOs."""

from dataclasses import dataclass
from typing import Any, List


@dataclass(frozen=True)
class EventsStatusReportData:
    events_by_status: List[dict]
    overdue_events: Any
    long_reviewing: Any
    completed_unchecked: Any
    participation_stats: List[dict]
    all_events: Any
    courses: Any
    active_report: str = 'events-status'
    active_course_pk: Any = None


@dataclass(frozen=True)
class WorkAnalysisReportData:
    works_analysis: List[dict]
    summary_stats: dict
    courses: Any
    active_report: str = 'work-analysis'
    active_course_pk: Any = None


@dataclass(frozen=True)
class StudentPerformanceReportData:
    students_stats: List[dict]
    groups: Any
    selected_group: Any
    summary_stats: dict
    courses: Any
    active_report: str = 'student-performance'
    active_course_pk: Any = None
