"""Port for reports dashboard data."""

from abc import ABC, abstractmethod

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import ReportsDashboardSource


class IReportsDashboardRepository(ABC):
    @abstractmethod
    def get_reports_dashboard_source(
        self,
        year: AcademicYearRef | None,
    ) -> ReportsDashboardSource:
        """Return normalized facts for the reports dashboard."""
