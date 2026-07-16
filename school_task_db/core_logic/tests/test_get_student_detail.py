from unittest import TestCase

from core_logic.use_cases.get_student_detail import GetStudentDetailUseCase
from core_logic.use_cases.get_student_group_detail import (
    GetStudentGroupDetailUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.detail_students = ['student-1']
        self.detail_student_groups = ['group-1']

    def get_detail_students(self):
        return self.detail_students

    def get_detail_student_groups(self):
        return self.detail_student_groups


class GetStudentDetailUseCaseTests(TestCase):
    def test_get_queryset_returns_student_detail_queryset(self):
        repo = FakeStudentRepository()
        use_case = GetStudentDetailUseCase(student_repo=repo)

        self.assertEqual(use_case.get_queryset(), ['student-1'])


class GetStudentGroupDetailUseCaseTests(TestCase):
    def test_get_queryset_returns_student_group_detail_queryset(self):
        repo = FakeStudentRepository()
        use_case = GetStudentGroupDetailUseCase(student_repo=repo)

        self.assertEqual(use_case.get_queryset(), ['group-1'])
