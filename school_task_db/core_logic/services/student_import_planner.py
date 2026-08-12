"""Build deterministic student import changes from a database snapshot."""

from dataclasses import dataclass
from typing import Iterable

from core_logic.entities.student_import import (
    StudentImportAcademicYearCreate,
    StudentImportGroupCreate,
    StudentImportMembershipCreate,
    StudentImportPlan,
    StudentImportRow,
    StudentImportSnapshot,
    StudentImportStats,
    StudentImportStudentMutation,
)


@dataclass
class _StudentState:
    token: str
    last_name: str
    first_name: str
    middle_name: str
    email: str


class StudentImportPlanner:
    def build(
        self,
        rows: Iterable[StudentImportRow],
        snapshot: StudentImportSnapshot,
    ) -> StudentImportPlan:
        rows = tuple(rows)
        years_by_name = {year.name: year for year in snapshot.academic_years}
        active_year_name = next(
            (year.name for year in snapshot.academic_years if year.is_active),
            '',
        )
        groups_by_key = {
            (group.name, group.academic_year_name): f'existing:{group.pk}'
            for group in snapshot.groups
        }
        students = [
            _StudentState(
                token=f'existing:{student.pk}',
                last_name=student.last_name,
                first_name=student.first_name,
                middle_name=student.middle_name,
                email=student.email,
            )
            for student in snapshot.students
        ]
        memberships = {
            (f'existing:{item.group_id}', f'existing:{item.student_id}')
            for item in snapshot.memberships
        }

        years_to_create = []
        groups_to_create = []
        student_mutations = []
        memberships_to_create = []
        next_group_number = 1
        next_student_number = 1
        students_created = 0
        students_updated = 0

        for row in rows:
            year_name = row.academic_year_name or active_year_name
            if (
                row.academic_year_name
                and row.academic_year_name not in years_by_name
            ):
                is_active = not active_year_name
                years_to_create.append(
                    StudentImportAcademicYearCreate(
                        name=row.academic_year_name,
                        start_date=row.academic_year_start,
                        end_date=row.academic_year_end,
                        is_active=is_active,
                    )
                )
                years_by_name[row.academic_year_name] = years_to_create[-1]
                if is_active:
                    active_year_name = row.academic_year_name
                year_name = row.academic_year_name

            group_key = (row.group_name, year_name)
            group_token = groups_by_key.get(group_key)
            if group_token is None:
                group_token = f'new-group:{next_group_number}'
                next_group_number += 1
                groups_by_key[group_key] = group_token
                groups_to_create.append(
                    StudentImportGroupCreate(
                        token=group_token,
                        name=row.group_name,
                        academic_year_name=year_name,
                    )
                )

            student = self._find_student(students, row)
            if student is None:
                student = _StudentState(
                    token=f'new-student:{next_student_number}',
                    last_name=row.last_name,
                    first_name=row.first_name,
                    middle_name=row.middle_name,
                    email=row.email,
                )
                next_student_number += 1
                students.append(student)
                student_mutations.append(
                    self._student_mutation(student, operation='create')
                )
                students_created += 1
            elif self._student_has_changes(student, row):
                student.last_name = row.last_name
                student.first_name = row.first_name
                student.middle_name = row.middle_name
                student.email = row.email
                student_mutations.append(
                    self._student_mutation(student, operation='update')
                )
                students_updated += 1

            membership = (group_token, student.token)
            if membership not in memberships:
                memberships.add(membership)
                memberships_to_create.append(
                    StudentImportMembershipCreate(
                        group_token=group_token,
                        student_token=student.token,
                    )
                )

        stats = StudentImportStats(
            rows=len(rows),
            years_created=len(years_to_create),
            groups_created=len(groups_to_create),
            students_created=students_created,
            students_updated=students_updated,
            memberships_created=len(memberships_to_create),
        )
        return StudentImportPlan(
            academic_years_to_create=tuple(years_to_create),
            groups_to_create=tuple(groups_to_create),
            student_mutations=tuple(student_mutations),
            memberships_to_create=tuple(memberships_to_create),
            stats=stats,
        )

    @staticmethod
    def _find_student(students, row):
        if row.email:
            email = row.email.lower()
            student = next(
                (
                    item
                    for item in students
                    if item.email and item.email.lower() == email
                ),
                None,
            )
            if student is not None:
                return student
        return next(
            (
                item
                for item in students
                if item.last_name == row.last_name
                and item.first_name == row.first_name
                and item.middle_name == row.middle_name
            ),
            None,
        )

    @staticmethod
    def _student_has_changes(student, row):
        return (
            student.last_name != row.last_name
            or student.first_name != row.first_name
            or student.middle_name != row.middle_name
            or student.email != row.email
        )

    @staticmethod
    def _student_mutation(student, operation):
        return StudentImportStudentMutation(
            token=student.token,
            operation=operation,
            last_name=student.last_name,
            first_name=student.first_name,
            middle_name=student.middle_name,
            email=student.email,
        )
