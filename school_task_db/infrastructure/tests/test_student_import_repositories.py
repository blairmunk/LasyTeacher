import datetime as dt

from django.test import TestCase

from core.models import AcademicYear
from core_logic.entities.student_import import (
    ImportStudentsRequest,
    StudentImportRow,
)
from infrastructure.container import Container
from infrastructure.repositories.django_student_import_command_repo import (
    DjangoStudentImportCommandRepository,
)
from infrastructure.repositories.django_student_import_snapshot_repo import (
    DjangoStudentImportSnapshotRepository,
)
from students.models import Student, StudentGroup


def _row(last_name='Иванов', email='ivanov@example.test'):
    return StudentImportRow(
        row_number=2,
        group_name='8А',
        academic_year_name='2026-2027',
        academic_year_start=dt.date(2026, 9, 1),
        academic_year_end=dt.date(2027, 8, 31),
        last_name=last_name,
        first_name='Иван',
        middle_name='Петрович',
        email=email,
    )


class DjangoStudentImportRepositoryTests(TestCase):
    def test_snapshot_returns_clean_current_state(self):
        year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=dt.date(2026, 9, 1),
            end_date=dt.date(2027, 8, 31),
            is_active=True,
        )
        student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        group = StudentGroup.objects.create(
            name='8А',
            academic_year=year,
        )
        group.students.add(student)

        snapshot = (
            DjangoStudentImportSnapshotRepository()
            .get_student_import_snapshot()
        )

        self.assertEqual(snapshot.academic_years[0].name, '2026-2027')
        self.assertEqual(snapshot.groups[0].academic_year_name, '2026-2027')
        self.assertEqual(snapshot.students[0].last_name, 'Иванов')
        self.assertEqual(snapshot.memberships[0].group_id, str(group.pk))
        self.assertEqual(snapshot.memberships[0].student_id, str(student.pk))

    def test_use_case_applies_create_and_later_update_plan(self):
        container = Container()

        result = container.import_students_use_case().execute(
            ImportStudentsRequest(
                rows=(
                    _row(),
                    _row(last_name='Сидоров'),
                ),
            ),
        )

        student = Student.objects.get()
        year = AcademicYear.objects.get()
        group = StudentGroup.objects.get()
        self.assertEqual(result.status, 'imported')
        self.assertEqual(result.stats.students_created, 1)
        self.assertEqual(result.stats.students_updated, 1)
        self.assertEqual(student.last_name, 'Сидоров')
        self.assertEqual(student.email, 'ivanov@example.test')
        self.assertTrue(year.is_active)
        self.assertEqual(group.academic_year, year)
        self.assertEqual(list(group.students.all()), [student])

    def test_container_wires_separate_snapshot_and_command_adapters(self):
        container = Container()
        use_case = container.import_students_use_case()

        self.assertIsInstance(
            use_case.snapshot_repo,
            DjangoStudentImportSnapshotRepository,
        )
        self.assertIsInstance(
            use_case.command_repo,
            DjangoStudentImportCommandRepository,
        )
