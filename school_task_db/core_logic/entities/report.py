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


@dataclass(frozen=True)
class ReportsDashboardData:
    total_students: int
    total_events: int
    total_works: int
    total_courses: int
    total_marks: int
    average_score: float
    marks_last_month: int
    score_counts: dict
    events_planned: int
    events_completed: int
    events_graded: int
    monthly_labels: List[str]
    monthly_values: List[int]
    class_stats: List[dict]
    class_names: List[str]
    class_avg_scores: List[float]
    class_completion: List[float]
    recent_events: Any
    event_status_counts: dict
    box_data: dict
    courses: Any
    active_report: str = 'dashboard'
    active_course_pk: Any = None


@dataclass(frozen=True)
class HeatmapOverviewData:
    groups: Any
    selected_group: Any
    students: List[Any]
    sections: List[str]
    courses: Any
    active_report: str = 'heatmap'
    active_course_pk: Any = None


@dataclass(frozen=True)
class HeatmapTopicMatrixData:
    columns: List[Any]
    rows: List[dict]
    col_averages: List[dict]


@dataclass(frozen=True)
class HeatmapCourseOverviewData:
    course: Any
    groups: Any
    selected_group: Any
    students: List[Any]
    course_works: List[Any]
    courses: Any
    active_report: str = 'heatmap-course'
    active_course_pk: Any = None


@dataclass(frozen=True)
class HeatmapCourseTimelineData:
    dates: List[str]
    averages: List[int]
    labels: List[str]
