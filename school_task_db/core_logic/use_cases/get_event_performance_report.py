"""Get a written performance report for one event."""

from core_logic.interfaces.event_performance_report_query_repo import (
    IEventPerformanceReportQueryRepository,
)
from core_logic.services.event_performance_report_service import (
    EventPerformanceReportService,
)


class GetEventPerformanceReportUseCase:
    def __init__(self, report_repo, report_service=None):
        self.report_repo: IEventPerformanceReportQueryRepository = report_repo
        self.report_service = report_service or EventPerformanceReportService()

    def execute(self, event_id: str):
        source = self.report_repo.get_event_report_source(event_id)
        if source is None:
            return None
        return self.report_service.build(source)
