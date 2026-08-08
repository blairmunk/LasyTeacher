"""Build events status report."""

from dataclasses import dataclass
from datetime import datetime

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report import EventsStatusReportData
from core_logic.interfaces.report_summary_repo import IReportSummaryRepository
from core_logic.services.report_summary_service import ReportSummaryService


@dataclass(frozen=True)
class EventsStatusReportRequest:
    year: AcademicYearRef | None = None
    current_date: datetime = None


class GetEventsStatusReportUseCase:
    def __init__(
        self,
        report_repo: IReportSummaryRepository,
        summary_service: ReportSummaryService | None = None,
    ):
        self.report_repo = report_repo
        self.summary_service = summary_service or ReportSummaryService()

    def execute(
        self,
        request: EventsStatusReportRequest,
    ) -> EventsStatusReportData:
        source = self.report_repo.get_events_status_source(
            year=request.year,
        )
        return self.summary_service.build_events_status(
            source,
            current_date=request.current_date,
        )
