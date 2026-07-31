"""Build reports dashboard data."""

from dataclasses import dataclass
from datetime import datetime

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report import ReportsDashboardData
from core_logic.interfaces.report_repo import IReportRepository
from core_logic.services.report_summary_service import ReportSummaryService


@dataclass(frozen=True)
class ReportsDashboardRequest:
    year: AcademicYearRef | None = None
    current_date: datetime | None = None


class GetReportsDashboardUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        summary_service: ReportSummaryService | None = None,
    ):
        self.report_repo = report_repo
        self.summary_service = summary_service or ReportSummaryService()

    def execute(self, request: ReportsDashboardRequest) -> ReportsDashboardData:
        source = self.report_repo.get_reports_dashboard_source(
            year=request.year,
        )
        return self.summary_service.build_reports_dashboard(
            source,
            current_date=request.current_date,
        )
