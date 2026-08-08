"""Report repository interface."""

from abc import ABC, abstractmethod
from typing import Any

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report import (
    EventsStatusSource,
    HeatmapCourseOverviewData,
    HeatmapCourseTimelineSource,
    HeatmapDrilldownOverviewData,
    HeatmapMatrixSource,
    HeatmapOverviewData,
    HeatmapStudentDetailSource,
    HeatmapSubtopicDetailSource,
    HeatmapTopicMatrixData,
    JournalSource,
    JournalSelectData,
    ReportsDashboardSource,
    StudentPerformanceSource,
    TaskDBHealthSource,
    WorkAnalysisSource,
)


class IReportSummaryRepository(ABC):
    @abstractmethod
    def get_events_status_source(
        self,
        year: AcademicYearRef | None,
    ) -> EventsStatusSource:
        """Return normalized facts for the events status report."""

    @abstractmethod
    def get_work_analysis_source(
        self,
        year: AcademicYearRef | None,
    ) -> WorkAnalysisSource:
        """Return normalized facts for work analysis."""

    @abstractmethod
    def get_student_performance_source(
        self,
        year: AcademicYearRef | None,
        group_id: Any,
    ) -> StudentPerformanceSource:
        """Return normalized facts for the student performance report."""

    @abstractmethod
    def get_reports_dashboard_source(
        self,
        year: AcademicYearRef | None,
    ) -> ReportsDashboardSource:
        """Return normalized facts for the reports dashboard."""


class IJournalRepository(ABC):
    @abstractmethod
    def get_journal_select(
        self,
        year: AcademicYearRef | None,
    ) -> JournalSelectData:
        """Return course-group pairs available for journal view."""

    @abstractmethod
    def get_journal_source(
        self,
        course_id: Any,
        group_id: Any,
        year: AcademicYearRef | None,
    ) -> JournalSource:
        """Return normalized facts for the class journal."""


class ITaskDBHealthRepository(ABC):
    @abstractmethod
    def get_task_db_health_source(self) -> TaskDBHealthSource:
        """Return normalized facts for task database diagnostics."""


class IHeatmapRepository(ABC):

    @abstractmethod
    def get_heatmap_overview(self, group_id: Any) -> HeatmapOverviewData:
        """Return base heatmap data."""

    @abstractmethod
    def get_heatmap_topic_matrix_source(
        self,
        student_ids: list,
        section_filter: str,
    ) -> HeatmapMatrixSource:
        """Return normalized facts for the student-topic matrix."""

    @abstractmethod
    def get_heatmap_course_overview(
        self,
        course_id: Any,
        group_id: Any,
    ) -> HeatmapCourseOverviewData:
        """Return base course heatmap data."""

    @abstractmethod
    def get_heatmap_course_topic_matrix_source(
        self,
        student_ids: list,
        work_ids: list,
    ) -> HeatmapMatrixSource:
        """Return normalized facts for a course student-topic matrix."""

    @abstractmethod
    def get_heatmap_course_timeline_source(
        self,
        student_ids: list,
        work_ids: list,
    ) -> HeatmapCourseTimelineSource:
        """Return normalized facts for a course timeline chart."""

    @abstractmethod
    def get_heatmap_drilldown_overview(
        self,
        topic_id: Any,
        group_id: Any,
    ) -> HeatmapDrilldownOverviewData:
        """Return base topic drilldown heatmap data."""

    @abstractmethod
    def get_heatmap_subtopic_matrix_source(
        self,
        student_ids: list,
        topic_id: Any,
    ) -> HeatmapMatrixSource:
        """Return normalized facts for the student-subtopic matrix."""

    @abstractmethod
    def get_heatmap_subtopic_detail_source(
        self,
        subtopic_id: Any,
        group_id: Any,
    ) -> HeatmapSubtopicDetailSource:
        """Return normalized facts for detailed subtopic analysis."""

    @abstractmethod
    def get_heatmap_student_detail_source(
        self,
        topic_id: Any,
        student_id: Any,
        subtopic_id: Any,
    ) -> HeatmapStudentDetailSource:
        """Return normalized facts for one student's topic history."""


class IReportRepository(
    IReportSummaryRepository,
    IJournalRepository,
    ITaskDBHealthRepository,
    IHeatmapRepository,
):
    """Compatibility aggregate for adapters implementing every report port."""
