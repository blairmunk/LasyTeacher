"""Django task import service."""

import time

from infrastructure.importers.tasks import TaskImporter
from core.models import ImportLog
from core_logic.services.import_log_service import ImportLogService
from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportPreviewResult,
    TaskImportRequest,
    TaskImportResult,
)
from core_logic.interfaces.task_import import ITaskImportService


class DjangoTaskImportService(ITaskImportService):
    def preview_import(
        self,
        request: TaskImportPreviewRequest,
    ) -> TaskImportPreviewResult:
        try:
            importer, context = self._run_import(
                data=request.data,
                mode='update',
                dry_run=True,
                verbose=False,
                create_missing=True,
            )
            summary = self._summarize_import(importer, context)

            return TaskImportPreviewResult(
                preview=summary['preview'],
            )
        except Exception as exc:
            return TaskImportPreviewResult(warning=f'Ошибка dry-run: {str(exc)}')

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
            importer, context = self._run_import(
                data=request.data,
                mode=request.mode,
                dry_run=request.dry_run,
                verbose=True,
                create_missing=request.create_missing,
            )

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

    @staticmethod
    def _run_import(*, data, mode, dry_run, verbose, create_missing):
        importer = TaskImporter(
            mode=mode,
            dry_run=dry_run,
            verbose=verbose,
            create_missing=create_missing,
            output=lambda _message: None,
        )
        importer.validate_mode()
        context = importer.import_tasks_from_json(data)
        return importer, context

    @staticmethod
    def _summarize_import(importer, context):
        errors_count = getattr(importer.stats, 'errors', 0)
        error_messages = [
            str(error.get('message', error))
            for error in getattr(importer.stats, 'error_details', [])[:50]
        ]

        by_type = {
            action: dict(getattr(importer.stats, f'{action}_by_type', {}))
            for action in ('created', 'updated', 'skipped')
        }
        return {
            'created': by_type['created'].get('tasks', 0),
            'updated': by_type['updated'].get('tasks', 0),
            'skipped': by_type['skipped'].get('tasks', 0),
            'by_type': by_type,
            'errors': errors_count,
            'error_messages': error_messages,
            'context': context.get_stats_summary(),
            'context_counts': {
                'tasks': len(context.imported_tasks),
                'groups': len(context.imported_groups),
                'topics': len(context.imported_topics),
            },
            'preview': context.preview_summary,
        }

    def _complete_log(self, log, importer, context, duration_ms):
        summary = self._summarize_import(importer, context)

        log.tasks_created = summary['created']
        log.tasks_updated = summary['updated']
        log.tasks_skipped = summary['skipped']
        log.groups_created = summary['by_type']['created'].get('groups', 0)
        log.topics_created = summary['by_type']['created'].get('topics', 0)
        log.images_created = summary['by_type']['created'].get('images', 0)
        log.errors_count = summary['errors']
        log.details = {
            'importer_stats': {
                'created': summary['created'],
                'updated': summary['updated'],
                'skipped': summary['skipped'],
            },
            'operations_by_type': summary['by_type'],
            'context_stats': summary['context'],
            'context_counts': summary['context_counts'],
            'preview': summary['preview'],
        }
        log.error_messages = summary['error_messages']
        log.duration_ms = duration_ms
        log.status = (
            ImportLog.Status.SUCCESS if summary['errors'] == 0
            else ImportLog.Status.PARTIAL
        )
        log.save()

        return TaskImportResult(
            status='success',
            dry_run=log.dry_run,
            log_id=str(log.id),
            duration_ms=duration_ms,
            stats={
                'created': summary['created'],
                'updated': summary['updated'],
                'skipped': summary['skipped'],
                'errors': summary['errors'],
                'by_type': summary['by_type'],
                'context': summary['context'],
                'context_counts': summary['context_counts'],
                'preview': summary['preview'],
            },
            message=self._build_summary_message(log),
        )

    def _build_summary_message(self, log):
        prefix = "🔍 ПРЕВЬЮ (dry-run)" if log.dry_run else "✅ ИМПОРТ ЗАВЕРШЁН"
        lines = [
            prefix,
            f"Файл: {log.filename} ("
            f"{ImportLogService.file_size_human(log.file_size)})",
            f"Режим: {log.get_mode_display()}",
            f"Время: {ImportLogService.duration_human(log.duration_ms)}",
        ]
        if log.dry_run:
            preview = (log.details or {}).get('preview', {})
            file_counts = preview.get('file_counts', {})
            task_counts = preview.get('task_uuid_counts', {})
            dependency_counts = preview.get('dependency_counts', {})
            lines.extend([
                '',
                '📦 В файле:',
                f"  Заданий: {file_counts.get('tasks', 0)}",
                f"  Групп аналогов: {file_counts.get('groups', 0)}",
                f"  Тем: {file_counts.get('topics', 0)}",
                f"  Источников: {file_counts.get('sources', 0)}",
                f"  Изображений: {file_counts.get('images', 0)}",
                '',
                '🔎 UUID заданий:',
                f"  Новых: {task_counts.get('new', 0)}",
                f"  Уже существуют: {task_counts.get('existing', 0)}",
                f"  Некорректных: {task_counts.get('invalid', 0)}",
                '',
                '🔗 Зависимости:',
                '  Отсутствующих тем: '
                f"{dependency_counts.get('missing_topics', 0)}",
                '  Отсутствующих подтем: '
                f"{dependency_counts.get('missing_subtopics', 0)}",
                '  Отсутствующих групп: '
                f"{dependency_counts.get('missing_groups', 0)}",
                '  Проблемных ссылок: '
                f"{dependency_counts.get('broken_references', 0)}",
                '  Классификаций не найдено: '
                f"{dependency_counts.get('missing_classifications', 0)}",
            ])
        else:
            lines.extend([
                '',
                '📊 Результаты:',
                f"  Создано: {log.tasks_created}",
                f"  Обновлено: {log.tasks_updated}",
                f"  Пропущено: {log.tasks_skipped}",
                '',
                '📦 В контексте:',
                f"  Групп аналогов: {log.groups_created}",
                f"  Тем: {log.topics_created}",
            ])
        if log.errors_count > 0:
            lines.append(f"\n❌ Ошибок: {log.errors_count}")
            for error in (log.error_messages or [])[:5]:
                lines.append(f"  • {error}")
        return "\n".join(lines)
