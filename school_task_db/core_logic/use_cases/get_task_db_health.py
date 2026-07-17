"""Build task database health report data."""

from core_logic.entities.report import TaskDBHealthData
from core_logic.interfaces.report_repo import IReportRepository


class GetTaskDBHealthUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(self) -> TaskDBHealthData:
        return self.report_repo.get_task_db_health()
