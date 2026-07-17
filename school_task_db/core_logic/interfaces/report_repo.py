"""Report repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from core_logic.entities.report import (
    EventsStatusReportData,
    HeatmapOverviewData,
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
