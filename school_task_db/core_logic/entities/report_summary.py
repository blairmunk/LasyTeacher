"""DTOs for dashboard and summary reports."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Mapping, Optional

from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportEventRef,
    ReportGroupRef,
    ReportMarkFact,
    ReportStudentRef,
    ReportWorkRef,
)


@dataclass(frozen=True)
class StudentPerformanceParticipationFact:
    status: str
    created_at: Any


@dataclass(frozen=True)
class StudentPerformanceItemSource:
    student: ReportStudentRef
    participations: List[StudentPerformanceParticipationFact]
    marks: List[ReportMarkFact]


@dataclass(frozen=True)
class StudentPerformanceSource:
    students: List[StudentPerformanceItemSource]
    groups: List[ReportGroupRef]
    selected_group: ReportGroupRef | None
    courses: List[ReportCourseRef]

@dataclass(frozen=True)
class WorkAnalysisItemSource:
    work: ReportWorkRef
    events_count: int
    marks: List[ReportMarkFact]
    events: List['ReportEventRef'] = field(default_factory=list)


@dataclass(frozen=True)
class WorkAnalysisSource:
    works: List[WorkAnalysisItemSource]
    courses: List[ReportCourseRef]


@dataclass(frozen=True)
class EventsStatusSource:
    events: List[ReportEventRef]
    participation_statuses: List[str]
    courses: List[ReportCourseRef]


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
    score_counts: Mapping[int, int]
    events_planned: int
    events_completed: int
    events_graded: int
    monthly_labels: tuple[str, ...]
    monthly_values: tuple[int, ...]
    class_stats: tuple['DashboardClassStat', ...]
    class_names: tuple[str, ...]
    class_avg_scores: tuple[float, ...]
    class_completion: tuple[float, ...]
    recent_events: tuple[ReportEventRef, ...]
    event_status_counts: Mapping[str, int]
    box_data: Mapping[str, tuple[int, ...]]
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'dashboard'
    active_course_pk: Optional[str] = None


@dataclass(frozen=True)
class DashboardParticipationFact:
    student_id: str
    event_id: str
    status: str


@dataclass(frozen=True)
class DashboardMarkFact:
    student_id: str
    event_id: str
    score: int | None
    checked_at: Optional[datetime] = None


@dataclass(frozen=True)
class DashboardCourseGroupRef:
    course_id: str
    course_name: str
    group_id: str
    group_name: str


@dataclass(frozen=True)
class DashboardClassStat:
    id: str
    name: str
    students_count: int
    total_participations: int
    completed_participations: int
    average_score: float
    completion_rate: float
    heatmap_links: tuple[DashboardCourseGroupRef, ...] = field(
        default_factory=tuple,
    )


@dataclass(frozen=True)
class DashboardGroupSource:
    group: ReportGroupRef
    student_ids: tuple[str, ...]
    course_links: tuple[DashboardCourseGroupRef, ...]


@dataclass(frozen=True)
class ReportsDashboardSource:
    total_students: int
    total_works: int
    events: tuple[ReportEventRef, ...]
    participations: tuple[DashboardParticipationFact, ...]
    marks: tuple[DashboardMarkFact, ...]
    groups: tuple[DashboardGroupSource, ...]
    courses: tuple[ReportCourseRef, ...]
