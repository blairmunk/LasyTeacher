"""Prepare an uploaded task import submission and execute it."""

from core_logic.entities.task_import import (
    TaskImportExecutionSubmissionRequest,
    TaskImportResult,
)
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase
from core_logic.use_cases.prepare_task_import_file import (
    PrepareTaskImportExecutionSubmissionUseCase,
)


class ExecuteTaskImportSubmissionUseCase:
    def __init__(
        self,
        execute_import_use_case: ExecuteTaskImportUseCase,
        prepare_submission_use_case:
            PrepareTaskImportExecutionSubmissionUseCase | None = None,
    ):
        self.prepare_submission_use_case = (
            prepare_submission_use_case
            or PrepareTaskImportExecutionSubmissionUseCase()
        )
        self.execute_import_use_case = execute_import_use_case

    def execute(
        self,
        request: TaskImportExecutionSubmissionRequest,
    ) -> TaskImportResult:
        prepared_submission = self.prepare_submission_use_case.execute(request)
        if not prepared_submission.success:
            return TaskImportResult(
                status='error',
                error=prepared_submission.error,
            )

        return self.execute_import_use_case.execute(
            prepared_submission.import_request,
        )
