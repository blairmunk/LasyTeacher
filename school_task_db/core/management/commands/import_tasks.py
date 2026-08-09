"""Import tasks from JSON through the clean task import use case."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core_logic.entities.task_import import (
    TaskImportFileRequest,
    TaskImportRequest,
)
from infrastructure.container import container


class Command(BaseCommand):
    help = 'Импорт заданий из JSON с полной поддержкой UUID'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='JSON файл с заданиями')
        parser.add_argument(
            '--mode',
            choices=['strict', 'update', 'skip'],
            default='update',
            help='Режим обработки существующих UUID',
        )
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Создавать отсутствующие группы автоматически',
        )
        parser.add_argument(
            '--create-topics',
            action='store_true',
            help='Создавать отсутствующие темы автоматически',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Предварительный просмотр',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Показать подробную итоговую статистику',
        )

    def handle(self, *args, **options):
        json_file = Path(options['json_file'])
        if not json_file.is_file():
            raise CommandError(f'JSON файл не найден: {json_file}')

        try:
            content = json_file.read_bytes()
        except OSError as error:
            raise CommandError(f'Ошибка чтения файла: {error}') from error

        prepared_file = container.prepare_task_import_file_use_case().execute(
            TaskImportFileRequest(
                filename=json_file.name,
                file_size=len(content),
                content=content,
            ),
        )
        if not prepared_file.success:
            raise CommandError(prepared_file.error)

        result = container.execute_task_import_use_case().execute(
            TaskImportRequest(
                data=prepared_file.data,
                filename=prepared_file.filename,
                file_size=prepared_file.file_size,
                mode=options['mode'],
                dry_run=options['dry_run'],
                create_missing=(
                    options['create_groups'] or options['create_topics']
                ),
            ),
        )
        if not result.success:
            raise CommandError(result.error or 'Не удалось импортировать задания')

        self.stdout.write(result.message)
        if options['verbose']:
            self.stdout.write(
                json.dumps(
                    result.stats,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
            )
