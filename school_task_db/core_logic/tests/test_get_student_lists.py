from unittest import TestCase

from core_logic.use_cases.get_student_group_list import GetStudentGroupListUseCase
from core_logic.use_cases.get_student_list import GetStudentListUseCase


class FakeStudentRepository:
    def __init__(self):
        self.students = ['student-1']
        self.student_groups = ['group-1']
        self.students_year = None
        self.groups_year = None

    def get_list_students(self, year=None):
        self.students_year = year
        return self.students

    def get_list_student_groups(self, year=None):
        self.groups_year = year
        return self.student_groups


class GetStudentListUseCaseTests(TestCase):
    def test_execute_returns_student_list_data(self):
        repo = FakeStudentRepository()
        use_case = GetStudentListUseCase(student_repo=repo)

        data = use_case.execute(year='year-1')

        self.assertEqual(data.students, ['student-1'])
        self.assertEqual(repo.students_year, 'year-1')


class GetStudentGroupListUseCaseTests(TestCase):
    def test_execute_returns_student_group_list_data(self):
        repo = FakeStudentRepository()
        use_case = GetStudentGroupListUseCase(student_repo=repo)

        data = use_case.execute(year='year-1')

        self.assertEqual(data.student_groups, ['group-1'])
        self.assertEqual(repo.groups_year, 'year-1')
