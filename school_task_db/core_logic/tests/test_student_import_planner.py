import datetime as dt
from contextlib import contextmanager
from unittest import TestCase

from core_logic.entities.student_import import (
    ImportStudentsRequest,
    StudentImportAcademicYearRef,
    StudentImportGroupRef,
    StudentImportMembershipRef,
    StudentImportRow,
    StudentImportSnapshot,
    StudentImportStudentRef,
)
from core_logic.services.student_import_planner import StudentImportPlanner
from core_logic.use_cases.import_students import ImportStudentsUseCase


def _row(
    last_name='Иванов',
    first_name='Иван',
    group_name='8А',
    year_name='2026-2027',
    email='',
):
    return StudentImportRow(
        row_number=2,
        group_name=group_name,
        academic_year_name=year_name,
        academic_year_start=(
            dt.date(2026, 9, 1) if year_name else None
        ),
        academic_year_end=(
            dt.date(2027, 8, 31) if year_name else None
        ),
        last_name=last_name,
        first_name=first_name,
        email=email,
    )


class StudentImportPlannerTests(TestCase):
    def test_plans_unique_year_group_students_and_memberships(self):
        rows = (
            _row(email='ivanov@example.test'),
            _row(last_name='Петрова', first_name='Анна'),
        )

        plan = StudentImportPlanner().build(rows, StudentImportSnapshot())

        self.assertEqual(plan.stats.rows, 2)
        self.assertEqual(plan.stats.years_created, 1)
        self.assertEqual(plan.stats.groups_created, 1)
        self.assertEqual(plan.stats.students_created, 2)
        self.assertEqual(plan.stats.memberships_created, 2)
        self.assertTrue(plan.academic_years_to_create[0].is_active)

    def test_uses_active_year_when_row_year_is_empty(self):
        snapshot = StudentImportSnapshot(
            academic_years=(
                StudentImportAcademicYearRef(
                    pk='year-1',
                    name='2026-2027',
                    is_active=True,
                ),
            ),
        )

        plan = StudentImportPlanner().build(
            (_row(year_name=''),),
            snapshot,
        )

        self.assertEqual(plan.stats.years_created, 0)
        self.assertEqual(
            plan.groups_to_create[0].academic_year_name,
            '2026-2027',
        )

    def test_does_not_create_year_when_no_year_is_available(self):
        plan = StudentImportPlanner().build(
            (_row(year_name=''),),
            StudentImportSnapshot(),
        )

        self.assertEqual(plan.stats.years_created, 0)
        self.assertEqual(plan.groups_to_create[0].academic_year_name, '')

    def test_preserves_existing_entities_and_membership(self):
        snapshot = StudentImportSnapshot(
            academic_years=(
                StudentImportAcademicYearRef(
                    pk='year-1',
                    name='2026-2027',
                    is_active=True,
                ),
            ),
            groups=(
                StudentImportGroupRef(
                    pk='group-1',
                    name='8А',
                    academic_year_name='2026-2027',
                ),
            ),
            students=(
                StudentImportStudentRef(
                    pk='student-1',
                    last_name='Иванов',
                    first_name='Иван',
                    email='ivanov@example.test',
                ),
            ),
            memberships=(
                StudentImportMembershipRef(
                    group_id='group-1',
                    student_id='student-1',
                ),
            ),
        )

        plan = StudentImportPlanner().build(
            (_row(email='ivanov@example.test'),),
            snapshot,
        )

        self.assertEqual(plan.stats.years_created, 0)
        self.assertEqual(plan.stats.groups_created, 0)
        self.assertEqual(plan.stats.students_created, 0)
        self.assertEqual(plan.stats.students_updated, 0)
        self.assertEqual(plan.stats.memberships_created, 0)

    def test_updates_planned_student_on_later_email_match(self):
        rows = (
            _row(email='student@example.test'),
            _row(last_name='Сидоров', email='student@example.test'),
        )

        plan = StudentImportPlanner().build(rows, StudentImportSnapshot())

        self.assertEqual(plan.stats.students_created, 1)
        self.assertEqual(plan.stats.students_updated, 1)
        self.assertEqual(
            [item.operation for item in plan.student_mutations],
            ['create', 'update'],
        )
        self.assertEqual(
            plan.student_mutations[0].token,
            plan.student_mutations[1].token,
        )


class _SnapshotRepo:
    def get_student_import_snapshot(self):
        return StudentImportSnapshot()


class _CommandRepo:
    def __init__(self):
        self.plan = None

    def apply_student_import_plan(self, plan):
        self.plan = plan


class _TransactionManager:
    def __init__(self):
        self.entered = 0

    @contextmanager
    def atomic(self):
        self.entered += 1
        yield


class ImportStudentsUseCaseTests(TestCase):
    def test_dry_run_returns_plan_stats_without_writes(self):
        command_repo = _CommandRepo()
        transaction_manager = _TransactionManager()
        use_case = ImportStudentsUseCase(
            snapshot_repo=_SnapshotRepo(),
            command_repo=command_repo,
            transaction_manager=transaction_manager,
        )

        result = use_case.execute(
            ImportStudentsRequest(rows=(_row(),), dry_run=True),
        )

        self.assertEqual(result.status, 'planned')
        self.assertEqual(result.stats.students_created, 1)
        self.assertIsNone(command_repo.plan)
        self.assertEqual(transaction_manager.entered, 0)

    def test_applies_plan_inside_transaction(self):
        command_repo = _CommandRepo()
        transaction_manager = _TransactionManager()
        use_case = ImportStudentsUseCase(
            snapshot_repo=_SnapshotRepo(),
            command_repo=command_repo,
            transaction_manager=transaction_manager,
        )

        result = use_case.execute(
            ImportStudentsRequest(rows=(_row(),)),
        )

        self.assertEqual(result.status, 'imported')
        self.assertIsNotNone(command_repo.plan)
        self.assertEqual(transaction_manager.entered, 1)
