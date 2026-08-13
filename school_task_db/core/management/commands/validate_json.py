"""Validate portable task-bank JSON files through the clean use case."""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core_logic.entities.task_import import TaskImportFileRequest
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonRequest,
)
from infrastructure.container import container


class Command(BaseCommand):
    help = 'Проверить JSON-файлы банка заданий без изменения базы'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_files',
            nargs='+',
            help='JSON-файлы банка заданий',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Показать предупреждения и сводку',
        )

    def handle(self, *args, **options):
        invalid_files = []
        for file_name in options['json_files']:
            path = Path(file_name)
            self.stdout.write(f'Проверка: {path}')
            error = self._validate_file(path, verbose=options['verbose'])
            if error:
                invalid_files.append((path, error))
                self.stderr.write(self.style.ERROR(error))
            else:
                self.stdout.write(self.style.SUCCESS('Файл валиден.'))

        if invalid_files:
            names = ', '.join(str(path) for path, _error in invalid_files)
            raise CommandError(
                f'Не прошли проверку файлов: {len(invalid_files)} ({names})',
            )

    def _validate_file(self, path, *, verbose):
        if not path.is_file():
            return f'Файл не найден: {path}'
        try:
            content = path.read_bytes()
        except OSError as error:
            return f'Ошибка чтения файла: {error}'

        prepared = container.prepare_task_import_file_use_case().execute(
            TaskImportFileRequest(
                filename=path.name,
                file_size=len(content),
                content=content,
            ),
        )
        if not prepared.success:
            return prepared.error

        validation = container.validate_task_import_json_use_case().execute(
            ValidateTaskImportJsonRequest(data=prepared.data),
        )
        if not validation.is_valid:
            return '; '.join(validation.errors)

        if verbose:
            for warning in validation.warnings:
                self.stdout.write(self.style.WARNING(f'Предупреждение: {warning}'))
            summary = validation.summary
            self.stdout.write(
                'Сводка: '
                f'заданий={summary.get("tasks_total", 0)}, '
                f'групп={summary.get("groups_total", 0)}, '
                f'тем={summary.get("topics_total", 0)}, '
                f'изображений={summary.get("images_total", 0)}',
            )
        return ''
