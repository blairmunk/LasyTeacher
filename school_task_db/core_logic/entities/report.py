"""Report DTOs."""

from dataclasses import dataclass
from typing import Any, List


@dataclass(frozen=True)
class ReportStudentRef:
    pk: str
    full_name: str
    short_name: str = ''


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
class JournalSelectData:
    journal_links: List[dict]
    groups: Any
    courses: Any
    active_report: str = 'journal'
    active_course_pk: Any = None


@dataclass(frozen=True)
class JournalData:
    course: Any
    group: Any
    events: Any
    event_stats: List[dict]
    rows: List[dict]
    all_rows_count: int
    show_debts_only: bool
    total_debts: int
    students_with_debts: int
    courses: Any
    active_report: str = 'journal'
    active_course_pk: Any = None


@dataclass(frozen=True)
class TaskDBHealthData:
    stats: dict
    orphan_variants: dict
    empty_groups: dict
    coverage_issues: dict
    difficulty_dist: List[dict]
    ungrouped_tasks: dict
    fragile_groups: dict
    works_no_variants: dict
    works_no_spec: dict
    type_dist: List[dict]
    most_used_tasks: Any
    group_sizes: List[dict]
    unverified_tasks: dict
    no_source_tasks: dict
    no_grade_tasks: dict
    health: dict
    courses: Any
    active_report: str = 'db-health'
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


@dataclass(frozen=True)
class HeatmapDrilldownOverviewData:
    topic: Any
    groups: Any
    selected_group: Any
    students: List[Any]
    courses: Any
    active_report: str = 'heatmap'
    active_course_pk: Any = None


@dataclass(frozen=True)
class HeatmapSubtopicMatrixData:
    columns: List[Any]
    rows: List[dict]
    col_averages: List[dict]


@dataclass(frozen=True)
class HeatmapSubtopicDetailData:
    subtopic: Any
    topic: Any
    groups: Any
    selected_group: Any
    student_rows: List[dict]
    task_rows: List[dict]
    overall_pct: Any
    overall_css: str
    total_students: int
    students_with_data: int
    courses: Any
    active_report: str = 'heatmap'
    active_course_pk: Any = None


@dataclass(frozen=True)
class HeatmapStudentDetailData:
    topic: Any
    student: Any
    selected_subtopic: Any
    details: List[dict]
    subtopic_summary: List[dict]
    courses: Any
    active_report: str = 'heatmap'
    active_course_pk: Any = None
