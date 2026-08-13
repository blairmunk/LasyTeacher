"""Execute task import."""

from core_logic.entities.task_import import TaskImportRequest, TaskImportResult
from core_logic.interfaces.task_import import ITaskImportService
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonRequest,
    ValidateTaskImportJsonUseCase,
)


class ExecuteTaskImportUseCase:
    def __init__(
        self,
        task_import_service: ITaskImportService,
        validate_json_use_case: ValidateTaskImportJsonUseCase | None = None,
    ):
        self.task_import_service = task_import_service
        self.validate_json_use_case = (
            validate_json_use_case or ValidateTaskImportJsonUseCase()
        )

    def execute(self, request: TaskImportRequest) -> TaskImportResult:
        validation = self.validate_json_use_case.execute(
            ValidateTaskImportJsonRequest(data=request.data),
        )
        if not validation.is_valid:
            return TaskImportResult(
                status='error',
                error='; '.join(validation.errors),
            )
        return self.task_import_service.execute_import(request)
