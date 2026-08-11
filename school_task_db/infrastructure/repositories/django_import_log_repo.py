"""Django read adapter for task import history."""

from core.models import ImportLog
from core_logic.entities.core import ImportLogItem
from core_logic.interfaces.import_log_repo import IImportLogRepository
from core_logic.services.import_log_service import ImportLogService


class DjangoImportLogRepository(IImportLogRepository):
    def get_recent_import_logs(self, limit: int):
        return self._import_log_items(ImportLog.objects.all()[:limit])

    def get_import_logs(self):
        return self._import_log_items(ImportLog.objects.all())

    @staticmethod
    def _import_log_items(logs):
        return [
            ImportLogItem(
                filename=log.filename,
                mode_display=log.get_mode_display(),
                dry_run=log.dry_run,
                tasks_created=log.tasks_created,
                tasks_updated=log.tasks_updated,
                tasks_skipped=log.tasks_skipped,
                errors_count=log.errors_count,
                duration_ms=log.duration_ms,
                duration_human=ImportLogService.duration_human(
                    log.duration_ms,
                ),
                file_size_human=ImportLogService.file_size_human(
                    log.file_size,
                ),
                status_icon=ImportLogService.status_icon(log.status),
                created_at=log.created_at,
            )
            for log in logs
        ]
