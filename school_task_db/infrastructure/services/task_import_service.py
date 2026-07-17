"""Django task import service."""

import time

from core.importers.tasks import TaskImporter
from core.models import ImportLog
from core_logic.entities.task_import import TaskImportRequest, TaskImportResult
from core_logic.interfaces.task_import import ITaskImportService


class DjangoTaskImportService(ITaskImportService):
    def execute_import(self, request: TaskImportRequest) -> TaskImportResult:
        log = ImportLog.objects.create(
            filename=request.filename,
            mode=request.mode,
            dry_run=request.dry_run,
            file_size=request.file_size,
            status=ImportLog.Status.IMPORTING,
        )

        start_time = time.time()
        try:
            importer = TaskImporter(
                mode=request.mode,
                dry_run=request.dry_run,
                verbose=True,
                create_missing=request.create_missing,
            )
            importer.validate_mode()
            context = importer.import_tasks_from_json(request.data)

            duration_ms = int((time.time() - start_time) * 1000)
            return self._complete_log(
                log=log,
                importer=importer,
                context=context,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            log.status = ImportLog.Status.FAILED
            log.error_messages = [str(exc)]
            log.duration_ms = duration_ms
            log.save()

            return TaskImportResult(
                status='error',
                log_id=str(log.id),
                error=str(exc),
            )

    def _complete_log(self, log, importer, context, duration_ms):
        stats_created = getattr(importer.stats, 'created', 0)
        stats_updated = getattr(importer.stats, 'updated', 0)
        stats_skipped = getattr(importer.stats, 'skipped', 0)
        stats_errors_list = getattr(importer.stats, 'errors', [])

        if isinstance(stats_errors_list, list):
            errors_count = len(stats_errors_list)
            error_messages = [str(error) for error in stats_errors_list[:50]]
        elif isinstance(stats_errors_list, int):
            errors_count = stats_errors_list
            error_messages = []
        else:
            errors_count = 0
            error_messages = []

        tasks_in_context = len(getattr(context, 'imported_tasks', {}))
        groups_in_context = len(getattr(context, 'imported_groups', {}))
        topics_in_context = len(getattr(context, 'imported_topics', {}))

        context_stats = {}
        if hasattr(context, 'get_stats_summary'):
            context_stats = context.get_stats_summary()

        log.tasks_created = stats_created
        log.tasks_updated = stats_updated
        log.tasks_skipped = stats_skipped
        log.groups_created = groups_in_context
        log.topics_created = topics_in_context
        log.errors_count = errors_count
        log.details = {
            'importer_stats': {
                'created': stats_created,
                'updated': stats_updated,
                'skipped': stats_skipped,
            },
            'context_stats': context_stats,
            'context_counts': {
                'tasks': tasks_in_context,
                'groups': groups_in_context,
                'topics': topics_in_context,
            },
        }
        log.error_messages = error_messages
        log.duration_ms = duration_ms
        log.status = (
            ImportLog.Status.SUCCESS if errors_count == 0
            else ImportLog.Status.PARTIAL
        )
        log.save()

        return TaskImportResult(
            status='success',
            dry_run=log.dry_run,
            log_id=str(log.id),
            duration_ms=duration_ms,
            stats={
                'created': stats_created,
                'updated': stats_updated,
                'skipped': stats_skipped,
                'errors': errors_count,
                'context': context_stats,
                'context_counts': {
                    'tasks': tasks_in_context,
                    'groups': groups_in_context,
                    'topics': topics_in_context,
                },
            },
            message=self._build_summary_message(log),
        )

    def _build_summary_message(self, log):
        prefix = "🔍 ПРЕВЬЮ (dry-run)" if log.dry_run else "✅ ИМПОРТ ЗАВЕРШЁН"
        lines = [
            prefix,
            f"Файл: {log.filename} ({log.file_size_human})",
            f"Режим: {log.get_mode_display()}",
            f"Время: {log.duration_human}",
            "",
            "📊 Результаты:",
            f"  Создано: {log.tasks_created}",
            f"  Обновлено: {log.tasks_updated}",
            f"  Пропущено: {log.tasks_skipped}",
            "",
            "📦 В контексте:",
            f"  Групп аналогов: {log.groups_created}",
            f"  Тем: {log.topics_created}",
        ]
        if log.errors_count > 0:
            lines.append(f"\n❌ Ошибок: {log.errors_count}")
            for error in (log.error_messages or [])[:5]:
                lines.append(f"  • {error}")
        return "\n".join(lines)
