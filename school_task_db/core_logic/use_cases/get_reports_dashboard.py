"""Build reports dashboard data."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core_logic.entities.report import ReportsDashboardData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class ReportsDashboardRequest:
    year: Any = None
    current_date: datetime | None = None


class GetReportsDashboardUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(self, request: ReportsDashboardRequest) -> ReportsDashboardData:
        return self.report_repo.get_reports_dashboard(
            year=request.year,
            current_date=request.current_date,
        )
