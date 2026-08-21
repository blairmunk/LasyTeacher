"""Validate, execute, and journal a task import operation."""

from time import monotonic

from core_logic.entities.task_import import TaskImportRequest, TaskImportResult
from core_logic.interfaces.task_import import (
    ITaskImportLogRepository,
    ITaskImportRunner,
)
from core_logic.services.task_import_report_service import (
    TaskImportReportService,
)
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonRequest,
    ValidateTaskImportJsonUseCase,
)


class ExecuteTaskImportUseCase:
    def __init__(
        self,
        task_import_runner: ITaskImportRunner,
        task_import_log_repo: ITaskImportLogRepository,
        validate_json_use_case: ValidateTaskImportJsonUseCase | None = None,
        report_service: TaskImportReportService | None = None,
        clock=monotonic,
    ):
        self.task_import_runner = task_import_runner
        self.task_import_log_repo = task_import_log_repo
        self.validate_json_use_case = (
            validate_json_use_case or ValidateTaskImportJsonUseCase()
        )
        self.report_service = report_service or TaskImportReportService()
        self.clock = clock

    def execute(self, request: TaskImportRequest) -> TaskImportResult:
        validation = self.validate_json_use_case.execute(
            ValidateTaskImportJsonRequest(data=request.data),
        )
        if not validation.is_valid:
            return TaskImportResult(
                status='error',
                error='; '.join(validation.errors),
            )

        log_id = self.task_import_log_repo.start(request)
        started_at = self.clock()
        try:
            summary = self.task_import_runner.execute_import(request)
        except Exception as error:
            duration_ms = self._duration_ms(started_at)
            message = str(error)
            self.task_import_log_repo.fail(log_id, message, duration_ms)
            return TaskImportResult(
                status='error',
                log_id=log_id,
                duration_ms=duration_ms,
                error=message,
            )

        duration_ms = self._duration_ms(started_at)
        self.task_import_log_repo.complete(log_id, summary, duration_ms)
        return TaskImportResult(
            status='success',
            dry_run=request.dry_run,
            log_id=log_id,
            duration_ms=duration_ms,
            stats=summary.to_stats(),
            message=self.report_service.build(
                request,
                summary,
                duration_ms,
            ),
        )

    def _duration_ms(self, started_at) -> int:
        return max(0, int((self.clock() - started_at) * 1000))
