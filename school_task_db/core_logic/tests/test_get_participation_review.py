from unittest import TestCase

from core_logic.entities.review import (
    ReviewCommentRef,
    ReviewEventRef,
    ReviewMarkRef,
    ReviewParticipationRef,
    ReviewStudentRef,
    ReviewTaskRef,
    ReviewVariantTaskRef,
)
from core_logic.services.review_service import ReviewService
from core_logic.use_cases.get_participation_review import (
    GetParticipationReviewUseCase,
)


class FakeReviewRepository:
    def __init__(self):
        self.default_max_points = None
        self.event = ReviewEventRef(pk='event-1', name='КР')
        self.participation = ReviewParticipationRef(
            pk='p1',
            student=ReviewStudentRef(pk='s1', last_name='Иванов', first_name='Иван'),
            event=self.event,
        )

    def get_participation(self, participation_id):
        return self.participation

    def get_variant_tasks(self, participation_id):
        return [
            ReviewVariantTaskRef(
                task=ReviewTaskRef(id='task-1', text='Задание'),
                variant_task_id='variant-task-1',
                weight=2,
            ),
            ReviewVariantTaskRef(
                task=ReviewTaskRef(id='task-2', text='Задание 2'),
                variant_task_id='variant-task-2',
                weight=3,
            ),
            ReviewVariantTaskRef(
                task=ReviewTaskRef(id='task-demo', text='Демо'),
                variant_task_id='variant-task-demo',
                weight=10,
                is_assessable=False,
            ),
        ]

    def get_or_create_mark(self, participation_id, default_max_points):
        self.default_max_points = default_max_points
        return ReviewMarkRef(
            pk='mark-1',
            max_points=default_max_points,
            task_scores={'task-1': {'points': 1, 'max_points': 2}},
        )

    def get_review_participations(self, event_id):
        return [self.participation]

    def get_typical_comments(self, limit=10):
        return [ReviewCommentRef(text='Хорошо')]


class GetParticipationReviewUseCaseTests(TestCase):
    def test_execute_builds_review_screen_data(self):
        repo = FakeReviewRepository()
        use_case = GetParticipationReviewUseCase(
            review_repo=repo,
            review_service=ReviewService(),
        )

        result = use_case.execute('p1')

        self.assertEqual(repo.default_max_points, 5)
        self.assertEqual(result.participation.pk, 'p1')
        self.assertEqual(result.mark.max_points, 5)
        self.assertEqual(result.tasks_with_scores[0].points, 1)
        self.assertEqual(
            result.tasks_with_scores[0].variant_task_id,
            'variant-task-1',
        )
        self.assertEqual(result.tasks_with_scores[1].max_points, 3)
        self.assertEqual(
            [row.task.id for row in result.tasks_with_scores],
            ['task-1', 'task-2'],
        )
        self.assertEqual(result.typical_comments[0].text, 'Хорошо')
        self.assertEqual(result.current_position, 1)
        self.assertEqual(result.total_positions, 1)
