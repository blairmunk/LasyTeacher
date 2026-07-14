from unittest import TestCase

from core_logic.interfaces.event_repo import GradeParticipationResult
from core_logic.services.grading_service import GradingService
from core_logic.use_cases.grade_student_work import (
    GradeStudentWorkRequest,
    GradeStudentWorkUseCase,
)


class FakeEventRepository:
    def __init__(self):
        self.graded_params = None

    def grade_participation(self, params):
        self.graded_params = params
        return GradeParticipationResult(
            mark_id='mark-1',
            participation_id=params.participation_id,
            event_id='event-1',
            student_name='Иванов Иван',
            score=params.score,
            event_status='reviewing',
        )


class GradeStudentWorkUseCaseTests(TestCase):
    def test_execute_saves_grade_with_normalized_checked_by(self):
        repo = FakeEventRepository()
        use_case = GradeStudentWorkUseCase(
            event_repo=repo,
            grading_service=GradingService(),
        )

        result = use_case.execute(
            GradeStudentWorkRequest(
                participation_id='participation-1',
                score=4,
                points=8,
                max_points=10,
                teacher_comment='Хорошо',
                checked_by_display_name='',
                checked_by_username='teacher',
                task_scores={'task-1': {'points': 8, 'max_points': 10}},
            )
        )

        self.assertEqual(result.mark_id, 'mark-1')
        self.assertEqual(repo.graded_params.participation_id, 'participation-1')
        self.assertEqual(repo.graded_params.score, 4)
        self.assertEqual(repo.graded_params.checked_by, 'teacher')
        self.assertEqual(
            repo.graded_params.task_scores,
            {'task-1': {'points': 8, 'max_points': 10}},
        )
