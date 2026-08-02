"""Save teacher-authored sections of an event report."""

from core_logic.entities.event_performance_report import (
    SaveEventReportNarrativeParams,
)
from core_logic.interfaces.event_performance_report_repo import (
    IEventPerformanceReportRepository,
)


class SaveEventReportNarrativeUseCase:
    def __init__(self, report_repo: IEventPerformanceReportRepository):
        self.report_repo = report_repo

    def execute(self, params: SaveEventReportNarrativeParams):
        return self.report_repo.save_event_report_narrative(params)
