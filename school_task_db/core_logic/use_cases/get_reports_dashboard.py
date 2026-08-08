"""Build reports dashboard data."""

from dataclasses import dataclass
from datetime import datetime

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import ReportsDashboardData
from core_logic.interfaces.report_summary_repo import IReportSummaryRepository
from core_logic.services.reports_dashboard_service import ReportsDashboardService


@dataclass(frozen=True)
class ReportsDashboardRequest:
    year: AcademicYearRef | None = None
    current_date: datetime | None = None


class GetReportsDashboardUseCase:
    def __init__(
        self,
        report_repo: IReportSummaryRepository,
        dashboard_service: ReportsDashboardService | None = None,
    ):
        self.report_repo = report_repo
        self.dashboard_service = dashboard_service or ReportsDashboardService()

    def execute(self, request: ReportsDashboardRequest) -> ReportsDashboardData:
        source = self.report_repo.get_reports_dashboard_source(
            year=request.year,
        )
        return self.dashboard_service.build(
            source,
            current_date=request.current_date,
        )
