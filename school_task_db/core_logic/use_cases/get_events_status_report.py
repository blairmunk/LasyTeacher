"""Build events status report."""

from dataclasses import dataclass
from datetime import datetime

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import EventsStatusReportData
from core_logic.interfaces.events_status_repo import IEventsStatusRepository
from core_logic.services.events_status_service import EventsStatusService


@dataclass(frozen=True)
class EventsStatusReportRequest:
    year: AcademicYearRef | None = None
    current_date: datetime = None


class GetEventsStatusReportUseCase:
    def __init__(
        self,
        report_repo: IEventsStatusRepository,
        status_service: EventsStatusService | None = None,
    ):
        self.report_repo = report_repo
        self.status_service = status_service or EventsStatusService()

    def execute(
        self,
        request: EventsStatusReportRequest,
    ) -> EventsStatusReportData:
        source = self.report_repo.get_events_status_source(
            year=request.year,
        )
        return self.status_service.build(
            source,
            current_date=request.current_date,
        )
