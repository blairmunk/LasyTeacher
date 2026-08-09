"""Export the task bank through the clean export use case."""

import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core_logic.entities.task import TaskExportFilters
from core_logic.use_cases.export_tasks import ExportTasksRequest
from infrastructure.container import container


class Command(BaseCommand):
    help = 'Экспорт заданий в JSON-формат, совместимый с import_tasks'

    def add_arguments(self, parser):
        parser.add_argument('output_file', help='Выходной JSON-файл')
        parser.add_argument(
            '--include-groups',
            action='store_true',
            help='Включить описания групп аналогов',
        )
        parser.add_argument(
            '--include-topics',
            action='store_true',
            help='Включить отдельный список тем',
        )
        parser.add_argument('--filter-subject', help='Фильтр по предмету')
        parser.add_argument('--filter-grade', type=int, help='Фильтр по классу')
        parser.add_argument(
            '--limit',
            type=int,
            help='Ограничить количество заданий',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Показать подробную статистику',
        )

    def handle(self, *args, **options):
        self.stdout.write('📤 ЭКСПОРТ ЗАДАНИЙ В JSON:')
        self._write_filters(options)

        result = container.export_tasks_use_case().execute(
            ExportTasksRequest(
                filters=TaskExportFilters(
                    subject=options.get('filter_subject') or '',
                    grade=str(options.get('filter_grade') or ''),
                    limit=options.get('limit'),
                ),
                export_date=datetime.now().isoformat(),
                include_groups=options['include_groups'],
                include_topics=options['include_topics'],
            ),
        )
        payload = result.payload
        output_path = Path(options['output_file'])

        try:
            content = json.dumps(payload, ensure_ascii=False, indent=2)
            output_path.write_text(content, encoding='utf-8')
        except OSError as error:
            raise CommandError(f'Ошибка записи файла: {error}') from error

        self.stdout.write(
            self.style.SUCCESS(f'✅ Экспорт завершён: {output_path}'),
        )
        self.stdout.write(
            f'📊 Размер файла: {output_path.stat().st_size / 1024:.1f} КБ',
        )
        self.stdout.write(f"  📝 Заданий: {len(payload['tasks'])}")

        if options['verbose']:
            self._write_details(payload)

    def _write_filters(self, options):
        if options.get('filter_subject'):
            self.stdout.write(
                f"  📚 Предмет: {options['filter_subject']}",
            )
        if options.get('filter_grade'):
            self.stdout.write(f"  🎓 Класс: {options['filter_grade']}")
        if options.get('limit'):
            self.stdout.write(f"  📊 Ограничение: {options['limit']}")

    def _write_details(self, payload):
        self.stdout.write('  📦 Связанные данные:')
        self.stdout.write(
            f"    Групп: {len(payload.get('analog_groups', []))}",
        )
        self.stdout.write(f"    Тем: {len(payload.get('topics', []))}")
        self.stdout.write(f"    Источников: {len(payload.get('sources', []))}")
        self.stdout.write(
            f"    Изображений: {len(payload.get('task_images', []))}",
        )
