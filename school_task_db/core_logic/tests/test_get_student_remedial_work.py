from unittest import TestCase

from core_logic.entities.student import StudentRemedialWorkData
from core_logic.use_cases.get_student_remedial_work import (
    GetStudentRemedialWorkUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.requested_student_id = None
        self.remedial_data = StudentRemedialWorkData(
            remedial_groups=[{'group': 'group-1'}],
            weak_topics=[{'topic': 'topic-1'}],
            total_available=2,
            done_count=3,
        )

    def get_student_remedial_work_data(self, student_id):
        self.requested_student_id = student_id
        return self.remedial_data


class GetStudentRemedialWorkUseCaseTests(TestCase):
    def test_execute_returns_repository_data(self):
        repo = FakeStudentRepository()
        use_case = GetStudentRemedialWorkUseCase(student_repo=repo)

        result = use_case.execute('student-1')

        self.assertEqual(repo.requested_student_id, 'student-1')
        self.assertEqual(result, repo.remedial_data)
