"""DTOs for heatmap reports."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
    students: tuple[ReportStudentRef, ...]
    columns: tuple[ReportHeatmapColumnRef, ...]
    scores: tuple[HeatmapScoreFact, ...]


@dataclass(frozen=True)
class HeatmapMatrixCell:
    column: ReportHeatmapColumnRef
    pct: Optional[int]
    css: str
    points: Optional[float] = None
    max_points: Optional[float] = None


@dataclass(frozen=True)
class HeatmapMatrixRow:
    student: ReportStudentRef
    cells: tuple[HeatmapMatrixCell, ...]
    avg: Optional[int]
    avg_css: str


@dataclass(frozen=True)
class HeatmapColumnAverage:
    pct: Optional[int]
    css: str


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
    groups: tuple[ReportGroupRef, ...]
    selected_group: ReportGroupRef | None
    students: tuple[ReportStudentRef, ...]
    tasks: tuple[ReportTaskRef, ...]
    scores: tuple[HeatmapDetailScoreFact, ...]
    courses: tuple[ReportCourseRef, ...]


@dataclass(frozen=True)
class HeatmapStudentDetailSource:
    topic: ReportHeatmapColumnRef
    student: ReportStudentRef
    selected_subtopic: ReportHeatmapColumnRef | None
    subtopics: tuple[ReportHeatmapColumnRef, ...]
    tasks: tuple[ReportTaskRef, ...]
    scores: tuple[HeatmapDetailScoreFact, ...]
    courses: tuple[ReportCourseRef, ...]


@dataclass(frozen=True)
class HeatmapStudentTaskDetail:
    event: ReportActivityRef | None
    task: ReportTaskRef
    subtopic: ReportHeatmapColumnRef | None
    points: float
    max_points: float
    pct: int
    css: str


@dataclass(frozen=True)
class HeatmapStudentSubtopicSummary:
    subtopic: ReportHeatmapColumnRef
    pct: Optional[int]
    css: str
    is_selected: bool
    points: Optional[float] = None
    max_points: Optional[float] = None


@dataclass(frozen=True)
class HeatmapSubtopicStudentRow:
    student: ReportStudentRef
    pct: Optional[int]
    css: str
    events: tuple[str, ...]
    points: Optional[float] = None
    max_points: Optional[float] = None


@dataclass(frozen=True)
class HeatmapSubtopicTaskRow:
    task: ReportTaskRef
    avg_pct: int
    css: str
    students_count: int
    total_points: float
    total_max: float


@dataclass(frozen=True)
class HeatmapOverviewData:
    groups: tuple[ReportGroupRef, ...]
    selected_group: Optional[ReportGroupRef]
    students: tuple[ReportStudentRef, ...]
    sections: tuple[str, ...]
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'heatmap'
    active_course_pk: Optional[str] = None


@dataclass(frozen=True)
class HeatmapTopicMatrixData:
    columns: tuple[ReportHeatmapColumnRef, ...]
    rows: tuple[HeatmapMatrixRow, ...]
    col_averages: tuple[HeatmapColumnAverage, ...]


@dataclass(frozen=True)
class HeatmapCourseOverviewData:
    course: ReportCourseRef
    groups: tuple[ReportGroupRef, ...]
    selected_group: Optional[ReportGroupRef]
    students: tuple[ReportStudentRef, ...]
    course_works: tuple[ReportWorkRef, ...]
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'heatmap-course'
    active_course_pk: Optional[str] = None


@dataclass(frozen=True)
class HeatmapCourseTimelineData:
    dates: tuple[str, ...]
    averages: tuple[int, ...]
    labels: tuple[str, ...]


@dataclass(frozen=True)
class HeatmapTimelineEventRef:
    pk: str
    name: str
    planned_date: datetime


@dataclass(frozen=True)
class HeatmapTimelineMarkFact:
    event_id: str
    points: float
    max_points: float


@dataclass(frozen=True)
class HeatmapCourseTimelineSource:
    events: tuple[HeatmapTimelineEventRef, ...]
    marks: tuple[HeatmapTimelineMarkFact, ...]


@dataclass(frozen=True)
class HeatmapDrilldownOverviewData:
    topic: ReportHeatmapColumnRef
    groups: tuple[ReportGroupRef, ...]
    selected_group: Optional[ReportGroupRef]
    students: tuple[ReportStudentRef, ...]
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'heatmap'
    active_course_pk: Optional[str] = None


@dataclass(frozen=True)
class HeatmapSubtopicMatrixData:
    columns: tuple[ReportHeatmapColumnRef, ...]
    rows: tuple[HeatmapMatrixRow, ...]
    col_averages: tuple[HeatmapColumnAverage, ...]


@dataclass(frozen=True)
class HeatmapSubtopicDetailData:
    subtopic: ReportHeatmapColumnRef
    topic: ReportHeatmapColumnRef
    groups: tuple[ReportGroupRef, ...]
    selected_group: ReportGroupRef | None
    student_rows: tuple[HeatmapSubtopicStudentRow, ...]
    task_rows: tuple[HeatmapSubtopicTaskRow, ...]
    overall_pct: Optional[int]
    overall_css: str
    total_students: int
    students_with_data: int
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'heatmap'
    active_course_pk: Optional[str] = None


@dataclass(frozen=True)
class HeatmapStudentDetailData:
    topic: ReportHeatmapColumnRef
    student: ReportStudentRef
    selected_subtopic: ReportHeatmapColumnRef | None
    details: tuple[HeatmapStudentTaskDetail, ...]
    subtopic_summary: tuple[HeatmapStudentSubtopicSummary, ...]
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'heatmap'
    active_course_pk: Optional[str] = None
