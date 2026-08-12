"""Execute task import."""

from core_logic.entities.task_import import TaskImportRequest, TaskImportResult
from core_logic.interfaces.task_import import ITaskImportService
from core_logic.value_objects.task_transfer_format import (
    task_transfer_format_error,
)


class ExecuteTaskImportUseCase:
    def __init__(self, task_import_service: ITaskImportService):
        self.task_import_service = task_import_service

    def execute(self, request: TaskImportRequest) -> TaskImportResult:
        version_error = task_transfer_format_error(request.data)
        if version_error:
            return TaskImportResult(status='error', error=version_error)
        return self.task_import_service.execute_import(request)
