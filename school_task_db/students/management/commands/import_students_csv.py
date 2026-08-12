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
from django.db import transaction

from core.models import AcademicYear
from core_logic.entities.student_import import StudentImportValidationError
from core_logic.services.student_csv_import_parser import (
    parse_student_csv_rows,
)
from students.models import Student, StudentGroup


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
        stats = ImportStats()
        self._dry_run_year_names = set()
        self._dry_run_group_keys = set()
        self._dry_run_student_keys = set()
        self._dry_run_membership_keys = set()

        with transaction.atomic():
            for row in rows:
                self._import_row(row, dry_run=dry_run, stats=stats)

            if dry_run:
                transaction.set_rollback(True)

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

    def _import_row(self, row, dry_run, stats):
        stats.rows += 1

        academic_year = self._get_or_create_year(
            row,
            dry_run=dry_run,
            stats=stats,
        )
        group = self._get_or_create_group(
            row.group_name,
            academic_year=academic_year,
            academic_year_name=row.academic_year_name,
            dry_run=dry_run,
            stats=stats,
        )
        student = self._get_or_create_student(
            last_name=row.last_name,
            first_name=row.first_name,
            middle_name=row.middle_name,
            email=row.email,
            dry_run=dry_run,
            stats=stats,
        )

        if dry_run:
            membership_key = (
                _group_key(row.group_name, row.academic_year_name),
                _student_key(
                    row.last_name,
                    row.first_name,
                    row.middle_name,
                    row.email,
                ),
            )
            if group and student and group.students.filter(pk=student.pk).exists():
                return
            if membership_key not in self._dry_run_membership_keys:
                self._dry_run_membership_keys.add(membership_key)
                stats.memberships_created += 1
            return

        if not group.students.filter(pk=student.pk).exists():
            group.students.add(student)
            stats.memberships_created += 1

    def _get_or_create_year(self, row, dry_run, stats):
        name = row.academic_year_name
        if not name:
            return AcademicYear.objects.filter(is_active=True).first()

        academic_year = AcademicYear.objects.filter(name=name).first()
        if academic_year:
            return academic_year

        if dry_run:
            if name not in self._dry_run_year_names:
                self._dry_run_year_names.add(name)
                stats.years_created += 1
            return None

        stats.years_created += 1
        has_active_year = AcademicYear.objects.filter(is_active=True).exists()
        return AcademicYear.objects.create(
            name=name,
            start_date=row.academic_year_start,
            end_date=row.academic_year_end,
            is_active=not has_active_year,
        )

    def _get_or_create_group(
        self,
        name,
        academic_year,
        academic_year_name,
        dry_run,
        stats,
    ):
        group = StudentGroup.objects.filter(
            name=name,
            academic_year=academic_year,
        ).first()
        if group:
            return group

        if dry_run:
            group_key = _group_key(name, academic_year_name)
            if group_key not in self._dry_run_group_keys:
                self._dry_run_group_keys.add(group_key)
                stats.groups_created += 1
            return None

        stats.groups_created += 1
        return StudentGroup.objects.create(
            name=name,
            academic_year=academic_year,
        )

    def _get_or_create_student(
        self,
        last_name,
        first_name,
        middle_name,
        email,
        dry_run,
        stats,
    ):
        student = _find_student(
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            email=email,
        )
        if student is None:
            if dry_run:
                student_key = _student_key(
                    last_name,
                    first_name,
                    middle_name,
                    email,
                )
                if student_key not in self._dry_run_student_keys:
                    self._dry_run_student_keys.add(student_key)
                    stats.students_created += 1
                return None
            stats.students_created += 1
            return Student.objects.create(
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                email=email,
            )

        has_changes = (
            student.last_name != last_name
            or student.first_name != first_name
            or student.middle_name != middle_name
            or student.email != email
        )
        if has_changes:
            stats.students_updated += 1
            if not dry_run:
                student.last_name = last_name
                student.first_name = first_name
                student.middle_name = middle_name
                student.email = email
                student.save(
                    update_fields=[
                        'last_name',
                        'first_name',
                        'middle_name',
                        'email',
                        'updated_at',
                    ]
                )
        return student


class ImportStats:
    def __init__(self):
        self.rows = 0
        self.years_created = 0
        self.groups_created = 0
        self.students_created = 0
        self.students_updated = 0
        self.memberships_created = 0


def _group_key(name, academic_year_name):
    return name, academic_year_name


def _student_key(last_name, first_name, middle_name, email):
    if email:
        return 'email', email.lower()
    return 'name', last_name, first_name, middle_name


def _find_student(last_name, first_name, middle_name, email):
    if email:
        student = Student.objects.filter(email__iexact=email).first()
        if student:
            return student
    return Student.objects.filter(
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
    ).first()
