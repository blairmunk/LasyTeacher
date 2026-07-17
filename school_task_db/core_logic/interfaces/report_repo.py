"""Report repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from core_logic.entities.report import (
    EventsStatusReportData,
    HeatmapCourseOverviewData,
    HeatmapOverviewData,
    HeatmapTopicMatrixData,
    ReportsDashboardData,
    StudentPerformanceReportData,
    WorkAnalysisReportData,
)


class IReportRepository(ABC):
    @abstractmethod
    def get_events_status_report(
        self,
        year: Any,
        current_date: datetime,
    ) -> EventsStatusReportData:
        """Return events status report data."""

    @abstractmethod
    def get_work_analysis_report(self, year: Any) -> WorkAnalysisReportData:
        """Return work analysis report data."""

    @abstractmethod
    def get_student_performance_report(
        self,
        year: Any,
        group_id: Any,
    ) -> StudentPerformanceReportData:
        """Return student performance report data."""

    @abstractmethod
    def get_reports_dashboard(
        self,
        year: Any,
        current_date: datetime,
    ) -> ReportsDashboardData:
        """Return dashboard report data."""

    @abstractmethod
    def get_heatmap_overview(self, group_id: Any) -> HeatmapOverviewData:
        """Return base heatmap data."""

    @abstractmethod
    def get_heatmap_topic_matrix(
        self,
        student_ids: list,
        section_filter: str,
    ) -> HeatmapTopicMatrixData:
        """Return student-topic heatmap matrix data."""

    @abstractmethod
    def get_heatmap_course_overview(
        self,
        course_id: Any,
        group_id: Any,
    ) -> HeatmapCourseOverviewData:
        """Return base course heatmap data."""

    @abstractmethod
    def get_heatmap_course_topic_matrix(
        self,
        student_ids: list,
        work_ids: list,
    ) -> HeatmapTopicMatrixData:
        """Return student-topic heatmap matrix data for course works."""
