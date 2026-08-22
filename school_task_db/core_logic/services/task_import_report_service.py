"""Pure presentation of task import execution results."""

from core_logic.entities.task_import import (
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.services.import_log_service import ImportLogService
from core_logic.value_objects.task_import import task_import_mode_label


class TaskImportReportService:
    def build(
        self,
        request: TaskImportRequest,
        summary: TaskImportRunSummary,
        duration_ms: int,
    ) -> str:
        prefix = (
            '🔍 ПРЕВЬЮ (dry-run)'
            if request.dry_run
            else '✅ ИМПОРТ ЗАВЕРШЁН'
        )
        lines = [
            prefix,
            f'Файл: {request.filename} '
            f'({ImportLogService.file_size_human(request.file_size)})',
            f'Режим: {task_import_mode_label(request.mode)}',
            f'Время: {ImportLogService.duration_human(duration_ms)}',
        ]
        if request.dry_run:
            self._append_preview(lines, summary.preview)
        else:
            self._append_execution(lines, summary)
        if summary.errors:
            lines.append(f'\n❌ Ошибок: {summary.errors}')
            lines.extend(
                f'  • {error}'
                for error in summary.error_messages[:5]
            )
        if summary.warnings:
            lines.append(f'\n⚠️ Предупреждений: {summary.warnings}')
            lines.extend(
                f'  • {warning}'
                for warning in summary.warning_messages[:5]
            )
        return '\n'.join(lines)

    @staticmethod
    def _append_preview(lines, preview):
        file_counts = preview.get('file_counts', {})
        task_counts = preview.get('task_uuid_counts', {})
        dependencies = preview.get('dependency_counts', {})
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
            f"{dependencies.get('missing_topics', 0)}",
            '  Отсутствующих подтем: '
            f"{dependencies.get('missing_subtopics', 0)}",
            '  Отсутствующих групп: '
            f"{dependencies.get('missing_groups', 0)}",
            '  Проблемных ссылок: '
            f"{dependencies.get('broken_references', 0)}",
            '  Классификаций не найдено: '
            f"{dependencies.get('missing_classifications', 0)}",
        ])

    @staticmethod
    def _append_execution(lines, summary):
        lines.extend([
            '',
            '📊 Результаты:',
            f'  Создано: {summary.tasks_created}',
            f'  Обновлено: {summary.tasks_updated}',
            f'  Пропущено: {summary.tasks_skipped}',
            '',
            '📦 В контексте:',
            f"  Групп аналогов: {summary.context_counts.get('groups', 0)}",
            f"  Тем: {summary.context_counts.get('topics', 0)}",
            f"  Подтем: {summary.context_counts.get('subtopics', 0)}",
        ])
