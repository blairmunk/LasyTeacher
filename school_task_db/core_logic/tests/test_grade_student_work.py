from contextlib import contextmanager
from unittest import TestCase

from core_logic.entities.event import ParticipationGradingContext
from core_logic.entities.attempt_snapshot import AttemptSnapshotRef
from core_logic.entities.review import ReviewTaskRef, ReviewVariantTaskRef
from core_logic.interfaces.event_repo import GradeParticipationResult
from core_logic.services.grading_service import GradingService
from core_logic.use_cases.grade_student_work import (
    GradeStudentWorkRequest,
    GradeStudentWorkUseCase,
)


class FakeEventRepository:
    def __init__(self):
        self.graded_params = None
        self.context_request = None
        self.grading_context = ParticipationGradingContext(
            event_status='completed',
            other_active_participants=1,
            other_graded_participants=0,
        )

    def get_participation_grading_context(self, participation_id):
        self.context_request = participation_id
        return self.grading_context

    def save_participation_grade(self, params):
        self.graded_params = params
        return GradeParticipationResult(
            mark_id='mark-1',
            participation_id=params.participation_id,
            event_id='event-1',
            student_name='Иванов Иван',
            score=params.score,
            event_status=params.event_status or 'completed',
        )


class FakeTransactionManager:
    def __init__(self):
        self.entered = 0

    @contextmanager
    def atomic(self):
        self.entered += 1
        yield


class FakeReviewRepository:
    def __init__(self, variant_tasks=None):
        self.variant_tasks = variant_tasks or []
        self.request = None

    def get_variant_tasks(self, participation_id):
        self.request = participation_id
        return self.variant_tasks


class FakeAttemptSnapshotRepository:
    def __init__(self):
        self.mark_ids = []

    def capture_mark(self, mark_id):
        self.mark_ids.append(mark_id)
        return AttemptSnapshotRef(
            pk='attempt-1',
            participation_id='participation-1',
            mark_id=mark_id,
            revision=1,
        )


class GradeStudentWorkUseCaseTests(TestCase):
    def test_execute_saves_grade_with_normalized_checked_by(self):
        repo = FakeEventRepository()
        transaction_manager = FakeTransactionManager()
        attempt_snapshot_repo = FakeAttemptSnapshotRepository()
        use_case = GradeStudentWorkUseCase(
            event_repo=repo,
            review_repo=FakeReviewRepository(),
            grading_service=GradingService(),
            transaction_manager=transaction_manager,
            attempt_snapshot_repo=attempt_snapshot_repo,
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

        self.assertEqual(result.status, 'saved')
        self.assertEqual(result.grade.mark_id, 'mark-1')
        self.assertEqual(result.grade.event_status, 'reviewing')
        self.assertEqual(repo.context_request, 'participation-1')
        self.assertEqual(repo.graded_params.participation_id, 'participation-1')
        self.assertEqual(repo.graded_params.score, 4)
        self.assertEqual(repo.graded_params.checked_by, 'teacher')
        self.assertEqual(
            repo.graded_params.task_scores,
            {'task-1': {'points': 8, 'max_points': 10}},
        )
        self.assertEqual(repo.graded_params.event_status, 'reviewing')
        self.assertEqual(attempt_snapshot_repo.mark_ids, ['mark-1'])
        self.assertEqual(result.attempt_snapshot_id, 'attempt-1')
        self.assertEqual(transaction_manager.entered, 1)

    def test_execute_marks_event_graded_when_all_active_work_is_graded(self):
        repo = FakeEventRepository()
        repo.grading_context = ParticipationGradingContext(
            event_status='reviewing',
            other_active_participants=2,
            other_graded_participants=2,
        )
        use_case = GradeStudentWorkUseCase(
            event_repo=repo,
            review_repo=FakeReviewRepository(),
            grading_service=GradingService(),
            transaction_manager=FakeTransactionManager(),
        )

        result = use_case.execute(
            GradeStudentWorkRequest(
                participation_id='participation-1',
                score=5,
            )
        )

        self.assertEqual(result.grade.event_status, 'graded')
        self.assertEqual(repo.graded_params.event_status, 'graded')

    def test_execute_can_save_grade_without_syncing_event_status(self):
        repo = FakeEventRepository()
        use_case = GradeStudentWorkUseCase(
            event_repo=repo,
            review_repo=FakeReviewRepository(),
            grading_service=GradingService(),
            transaction_manager=FakeTransactionManager(),
        )

        result = use_case.execute(
            GradeStudentWorkRequest(
                participation_id='participation-1',
                score=3,
                sync_event_status=False,
            )
        )

        self.assertEqual(result.grade.event_status, 'completed')
        self.assertIsNone(repo.graded_params.event_status)

    def test_execute_rejects_invalid_mark_before_persistence(self):
        event_repo = FakeEventRepository()
        use_case = GradeStudentWorkUseCase(
            event_repo=event_repo,
            review_repo=FakeReviewRepository(),
            grading_service=GradingService(),
            transaction_manager=FakeTransactionManager(),
        )

        result = use_case.execute(
            GradeStudentWorkRequest(
                participation_id='participation-1',
                score=6,
                points=8,
                max_points=10,
            )
        )

        self.assertEqual(result.status, 'invalid')
        self.assertEqual(
            result.errors,
            ('Оценка должна быть от 1 до 5',),
        )
        self.assertIsNone(event_repo.context_request)
        self.assertIsNone(event_repo.graded_params)

    def test_execute_derives_totals_from_assessable_variant_snapshots(self):
        event_repo = FakeEventRepository()
        review_repo = FakeReviewRepository(
            variant_tasks=[
                ReviewVariantTaskRef(
                    task=ReviewTaskRef(id='task-1', text='Контрольное'),
                    variant_task_id='variant-task-1',
                    weight=3,
                    is_assessable=True,
                ),
                ReviewVariantTaskRef(
                    task=ReviewTaskRef(id='task-2', text='Демонстрация'),
                    variant_task_id='variant-task-2',
                    weight=5,
                    is_assessable=False,
                ),
            ],
        )
        use_case = GradeStudentWorkUseCase(
            event_repo=event_repo,
            review_repo=review_repo,
            grading_service=GradingService(),
            transaction_manager=FakeTransactionManager(),
        )

        use_case.execute(
            GradeStudentWorkRequest(
                participation_id='participation-1',
                score=4,
                points=99,
                max_points=99,
                task_scores={
                    'variant-task-1': {
                        'task_id': 'task-1',
                        'variant_task_id': 'variant-task-1',
                        'points': 10,
                        'max_points': 99,
                        'comment': 'Проверено',
                    },
                    'variant-task-2': {
                        'task_id': 'task-2',
                        'variant_task_id': 'variant-task-2',
                        'points': 5,
                        'max_points': 5,
                    },
                    'foreign-task': {
                        'points': 100,
                        'max_points': 100,
                    },
                },
            )
        )

        self.assertEqual(review_repo.request, 'participation-1')
        self.assertEqual(event_repo.graded_params.points, 3)
        self.assertEqual(event_repo.graded_params.max_points, 3)
        self.assertEqual(
            event_repo.graded_params.task_scores,
            {
                'variant-task-1': {
                    'task_id': 'task-1',
                    'variant_task_id': 'variant-task-1',
                    'points': 3,
                    'max_points': 3,
                    'comment': 'Проверено',
                },
            },
        )
