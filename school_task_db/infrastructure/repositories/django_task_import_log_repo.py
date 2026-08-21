"""Django command adapter for task import operation logs."""

from core.models import ImportLog
from core_logic.entities.task_import import (
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.interfaces.task_import import ITaskImportLogRepository


class DjangoTaskImportLogRepository(ITaskImportLogRepository):
    def start(self, request: TaskImportRequest) -> str:
        log = ImportLog.objects.create(
            filename=request.filename,
            mode=request.mode,
            dry_run=request.dry_run,
            file_size=request.file_size,
            status=ImportLog.Status.IMPORTING,
        )
        return str(log.pk)

    def complete(
        self,
        log_id: str,
        summary: TaskImportRunSummary,
        duration_ms: int,
    ) -> None:
        log = ImportLog.objects.get(pk=log_id)
        operation_counts = summary.operation_counts()
        log.tasks_created = summary.tasks_created
        log.tasks_updated = summary.tasks_updated
        log.tasks_skipped = summary.tasks_skipped
        log.groups_created = summary.created_by_type.get('groups', 0)
        log.topics_created = summary.created_by_type.get('topics', 0)
        log.images_created = summary.created_by_type.get('images', 0)
        log.errors_count = summary.errors
        log.details = {
            'operations_by_type': operation_counts,
            'context_counts': dict(summary.context_counts),
            'preview': dict(summary.preview),
        }
        log.error_messages = list(summary.error_messages)
        log.duration_ms = duration_ms
        log.status = summary.status
        log.save()

    def fail(self, log_id: str, error: str, duration_ms: int) -> None:
        log = ImportLog.objects.get(pk=log_id)
        log.status = ImportLog.Status.FAILED
        log.error_messages = [error]
        log.errors_count = 1
        log.duration_ms = duration_ms
        log.save()
