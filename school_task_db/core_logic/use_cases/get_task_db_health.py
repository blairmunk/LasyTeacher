"""Build task database health report data."""

from core_logic.entities.report import TaskDBHealthData
from core_logic.interfaces.report_repo import ITaskDBHealthRepository
from core_logic.services.report_summary_service import ReportSummaryService


class GetTaskDBHealthUseCase:
    def __init__(
        self,
        report_repo: ITaskDBHealthRepository,
        summary_service: ReportSummaryService | None = None,
    ):
        self.report_repo = report_repo
        self.summary_service = summary_service or ReportSummaryService()

    def execute(self) -> TaskDBHealthData:
        source = self.report_repo.get_task_db_health_source()
        return self.summary_service.build_task_db_health(source)
