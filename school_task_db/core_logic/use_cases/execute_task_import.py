"""Execute task import."""

from core_logic.entities.task_import import TaskImportRequest, TaskImportResult
from core_logic.interfaces.task_import import ITaskImportService


class ExecuteTaskImportUseCase:
    def __init__(self, task_import_service: ITaskImportService):
        self.task_import_service = task_import_service

    def execute(self, request: TaskImportRequest) -> TaskImportResult:
        return self.task_import_service.execute_import(request)
