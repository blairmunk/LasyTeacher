"""Build task database health report data."""

from core_logic.entities.task_db_health import TaskDBHealthData
from core_logic.interfaces.task_db_health_repo import ITaskDBHealthRepository
from core_logic.services.task_db_health_service import TaskDBHealthService


class GetTaskDBHealthUseCase:
    def __init__(
        self,
        report_repo: ITaskDBHealthRepository,
        health_service: TaskDBHealthService | None = None,
    ):
        self.report_repo = report_repo
        self.health_service = health_service or TaskDBHealthService()

    def execute(self) -> TaskDBHealthData:
        source = self.report_repo.get_task_db_health_source()
        return self.health_service.build(source)
