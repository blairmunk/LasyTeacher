"""Import students and student groups from a CSV file.

Usage:
    python manage.py import_students_csv students.csv --dry-run
    python manage.py import_students_csv students.csv

CSV columns:
    class,academic_year,last_name,first_name,middle_name,email
"""

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core_logic.entities.student_import import (
    ImportStudentsRequest,
    StudentImportValidationError,
)
from core_logic.services.student_csv_import_parser import (
    parse_student_csv_rows,
)
from infrastructure.container import container


class Command(BaseCommand):
    help = 'Импорт учеников и классов из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Проверить файл без сохранения',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_file'])
        dry_run = options['dry_run']
        if not csv_path.exists():
            raise CommandError(f'CSV файл не найден: {csv_path}')

        try:
            rows = parse_student_csv_rows(self._read_rows(csv_path))
        except StudentImportValidationError as error:
            raise CommandError(str(error)) from error
        result = container.import_students_use_case().execute(
            ImportStudentsRequest(rows=rows, dry_run=dry_run),
        )
        stats = result.stats

        self.stdout.write(
            'Импорт учеников: '
            f'строк={stats.rows}, '
            f'учебных годов создано={stats.years_created}, '
            f'учеников создано={stats.students_created}, '
            f'обновлено={stats.students_updated}, '
            f'классов создано={stats.groups_created}, '
            f'связей добавлено={stats.memberships_created}'
        )
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: изменения не сохранены.'))
        else:
            self.stdout.write(self.style.SUCCESS('Импорт завершен.'))

    def _read_rows(self, csv_path):
        try:
            with csv_path.open('r', encoding='utf-8-sig', newline='') as csv_file:
                reader = csv.DictReader(csv_file)
                if not reader.fieldnames:
                    raise CommandError('CSV файл не содержит заголовков.')
                return list(reader)
        except UnicodeDecodeError as error:
            raise CommandError(f'Не удалось прочитать CSV как UTF-8: {error}')
