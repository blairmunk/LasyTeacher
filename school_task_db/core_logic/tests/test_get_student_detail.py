from unittest import TestCase

from core_logic.entities.student import (
    StudentDetail,
    StudentGroupDetail,
    StudentGroupDetailStudent,
)
from core_logic.use_cases.get_student_detail import GetStudentDetailUseCase
from core_logic.use_cases.get_student_group_detail import (
    GetStudentGroupDetailUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.student = StudentDetail(
            pk='student-1',
            first_name='Иван',
            last_name='Петров',
            short_uuid='abcd1234',
            full_name='Петров Иван',
            short_name='Петров И.',
        )
        self.student_group = StudentGroupDetail(
            pk='group-1',
            name='9А',
            short_uuid='abcd1234',
            created_at=None,
        )

    def get_student(self, student_id):
        return self.student if student_id == self.student.pk else None

    def get_student_group(self, group_id):
        return self.student_group if group_id == self.student_group.pk else None


class GetStudentDetailUseCaseTests(TestCase):
    def test_execute_returns_student_detail_data(self):
        repo = FakeStudentRepository()
        use_case = GetStudentDetailUseCase(student_repo=repo)

        data = use_case.execute('student-1')

        self.assertEqual(data.student, repo.student)

    def test_execute_returns_empty_data_for_missing_student(self):
        repo = FakeStudentRepository()
        use_case = GetStudentDetailUseCase(student_repo=repo)

        data = use_case.execute('missing-student')

        self.assertIsNone(data.student)


class GetStudentGroupDetailUseCaseTests(TestCase):
    def test_student_group_detail_copies_students(self):
        students = [
            StudentGroupDetailStudent(
                pk='student-1',
                first_name='Иван',
                last_name='Петров',
            ),
        ]

        group = StudentGroupDetail(
            pk='group-1',
            name='9А',
            short_uuid='abcd1234',
            created_at=None,
            students=students,
        )
        students.clear()

        self.assertEqual(len(group.students), 1)
        self.assertEqual(group.students_count, 1)

    def test_execute_returns_student_group_detail_data(self):
        repo = FakeStudentRepository()
        use_case = GetStudentGroupDetailUseCase(student_repo=repo)

        data = use_case.execute('group-1')

        self.assertEqual(data.student_group, repo.student_group)

    def test_execute_returns_empty_data_for_missing_student_group(self):
        repo = FakeStudentRepository()
        use_case = GetStudentGroupDetailUseCase(student_repo=repo)

        data = use_case.execute('missing-group')

        self.assertIsNone(data.student_group)
