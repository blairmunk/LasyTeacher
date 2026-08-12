"""Save teacher-authored sections of an event report."""

from core_logic.entities.event_performance_report import (
    SaveEventReportNarrativeParams,
)
from core_logic.interfaces.event_report_narrative_command_repo import (
    IEventReportNarrativeCommandRepository,
)


class SaveEventReportNarrativeUseCase:
    def __init__(
        self,
        report_repo: IEventReportNarrativeCommandRepository,
    ):
        self.report_repo = report_repo

    def execute(self, params: SaveEventReportNarrativeParams):
        return self.report_repo.save_event_report_narrative(params)
