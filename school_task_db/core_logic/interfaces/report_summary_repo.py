"""Port for dashboard and summary report data."""

from abc import ABC, abstractmethod
from typing import Any

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report import (
    EventsStatusSource,
    ReportsDashboardSource,
    StudentPerformanceSource,
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
