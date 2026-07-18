from unittest import TestCase

from core_logic.entities.student import (
    SaveStudentGroupParams,
    SaveStudentGroupResult,
    SaveStudentParams,
    SaveStudentResult,
)
from core_logic.use_cases.save_student import (
    CreateStudentGroupUseCase,
    CreateStudentUseCase,
    UpdateStudentGroupUseCase,
    UpdateStudentUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.created_student = None
        self.updated_student = None
        self.created_group = None
        self.updated_group = None

    def create_student(self, params):
        self.created_student = params
        return SaveStudentResult(status='created', student_id='student-1')

    def update_student(self, params):
        self.updated_student = params
        return SaveStudentResult(status='updated', student_id=params.student_id)

    def create_student_group(self, params):
        self.created_group = params
        return SaveStudentGroupResult(status='created', group_id='group-1')

    def update_student_group(self, params):
        self.updated_group = params
        return SaveStudentGroupResult(status='updated', group_id=params.group_id)


class SaveStudentUseCaseTests(TestCase):
    def test_create_student_delegates_to_repository(self):
        repo = FakeStudentRepository()
        params = SaveStudentParams(
            first_name='Иван',
            last_name='Иванов',
            middle_name='Иванович',
            email='ivan@example.test',
        )

        result = CreateStudentUseCase(repo).execute(params)

        self.assertEqual(result.student_id, 'student-1')
        self.assertEqual(repo.created_student, params)

    def test_update_student_delegates_to_repository(self):
        repo = FakeStudentRepository()
        params = SaveStudentParams(
            student_id='student-1',
            first_name='Иван',
            last_name='Иванов',
        )

        result = UpdateStudentUseCase(repo).execute(params)

        self.assertEqual(result.status, 'updated')
        self.assertEqual(repo.updated_student, params)

    def test_create_student_group_delegates_to_repository(self):
        repo = FakeStudentRepository()
        params = SaveStudentGroupParams(
            name='9А',
            student_ids=['student-1', 'student-2'],
        )

        result = CreateStudentGroupUseCase(repo).execute(params)

        self.assertEqual(result.group_id, 'group-1')
        self.assertEqual(repo.created_group, params)

    def test_update_student_group_delegates_to_repository(self):
        repo = FakeStudentRepository()
        params = SaveStudentGroupParams(
            group_id='group-1',
            name='9Б',
            student_ids=['student-1'],
        )

        result = UpdateStudentGroupUseCase(repo).execute(params)

        self.assertEqual(result.status, 'updated')
        self.assertEqual(repo.updated_group, params)
