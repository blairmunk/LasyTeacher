"""Build task export payload."""

from dataclasses import dataclass

from core_logic.entities.task import TaskExportData, TaskExportFilters
from core_logic.interfaces.task_repo import ITaskRepository


@dataclass(frozen=True)
class ExportTasksRequest:
    filters: TaskExportFilters
    export_date: str


class ExportTasksUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, request: ExportTasksRequest) -> TaskExportData:
        return TaskExportData(
            payload=self.task_repo.build_task_export_payload(
                filters=request.filters,
                export_date=request.export_date,
            ),
        )
