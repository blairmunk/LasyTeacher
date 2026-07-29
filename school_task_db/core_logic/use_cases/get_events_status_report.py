"""Build events status report."""

from dataclasses import dataclass
from datetime import datetime

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report import EventsStatusReportData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class EventsStatusReportRequest:
    year: AcademicYearRef | None = None
    current_date: datetime = None


class GetEventsStatusReportUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: EventsStatusReportRequest,
    ) -> EventsStatusReportData:
        return self.report_repo.get_events_status_report(
            year=request.year,
            current_date=request.current_date,
        )
