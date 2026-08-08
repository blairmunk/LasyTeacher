"""DTOs for heatmap reports."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report_refs import (
    ReportActivityRef,
    ReportCourseRef,
    ReportGroupRef,
    ReportStudentRef,
    ReportTaskRef,
    ReportWorkRef,
)


@dataclass(frozen=True)
class ReportHeatmapColumnRef:
    pk: str
    name: str
    section: str = ''


@dataclass(frozen=True)
class HeatmapScoreFact:
    student_id: str
    column_id: str
    points: float
    max_points: float


@dataclass(frozen=True)
class HeatmapMatrixSource:
    students: List[ReportStudentRef]
    columns: List[ReportHeatmapColumnRef]
    scores: List[HeatmapScoreFact]


@dataclass(frozen=True)
class HeatmapDetailScoreFact:
    student_id: str
    task_id: str
    subtopic_id: str
    points: float
    max_points: float
    event: ReportActivityRef | None = None


@dataclass(frozen=True)
class HeatmapSubtopicDetailSource:
    subtopic: ReportHeatmapColumnRef
    topic: ReportHeatmapColumnRef
    groups: List[ReportGroupRef]
    selected_group: ReportGroupRef | None
    students: List[ReportStudentRef]
    tasks: List[ReportTaskRef]
    scores: List[HeatmapDetailScoreFact]
    courses: List[ReportCourseRef]


@dataclass(frozen=True)
class HeatmapStudentDetailSource:
    topic: ReportHeatmapColumnRef
    student: ReportStudentRef
    selected_subtopic: ReportHeatmapColumnRef | None
    subtopics: List[ReportHeatmapColumnRef]
    tasks: List[ReportTaskRef]
    scores: List[HeatmapDetailScoreFact]
    courses: List[ReportCourseRef]


@dataclass(frozen=True)
class HeatmapOverviewData:
    groups: List[ReportGroupRef]
    selected_group: ReportGroupRef | None
    students: List[ReportStudentRef]
    sections: List[str]
    courses: List[ReportCourseRef]
    active_report: str = 'heatmap'
    active_course_pk: Any = None


@dataclass(frozen=True)
class HeatmapTopicMatrixData:
    columns: List[Any]
    rows: List[dict]
    col_averages: List[dict]


@dataclass(frozen=True)
class HeatmapCourseOverviewData:
    course: ReportCourseRef
    groups: List[ReportGroupRef]
    selected_group: ReportGroupRef | None
    students: List[ReportStudentRef]
    course_works: List[ReportWorkRef]
    courses: List[ReportCourseRef]
    active_report: str = 'heatmap-course'
    active_course_pk: Any = None


@dataclass(frozen=True)
class HeatmapCourseTimelineData:
    dates: List[str]
    averages: List[int]
    labels: List[str]


@dataclass(frozen=True)
class HeatmapTimelineEventRef:
    pk: str
    name: str
    planned_date: Any


@dataclass(frozen=True)
class HeatmapTimelineMarkFact:
    event_id: str
    points: float
    max_points: float


@dataclass(frozen=True)
class HeatmapCourseTimelineSource:
    events: List[HeatmapTimelineEventRef]
    marks: List[HeatmapTimelineMarkFact]


@dataclass(frozen=True)
class HeatmapDrilldownOverviewData:
    topic: ReportHeatmapColumnRef
    groups: List[ReportGroupRef]
    selected_group: ReportGroupRef | None
    students: List[ReportStudentRef]
    courses: List[ReportCourseRef]
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
