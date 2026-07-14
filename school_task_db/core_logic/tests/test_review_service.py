from unittest import TestCase

from core_logic.entities.review import (
    ReviewEventRef,
    ReviewParticipationRef,
    ReviewStudentRef,
    ReviewTaskRef,
    ReviewVariantTaskRef,
)
from core_logic.services.review_service import ReviewService


class ReviewServiceTests(TestCase):
    def test_build_task_score_rows_uses_existing_scores_and_variant_weights(self):
        service = ReviewService()
        task = ReviewTaskRef(id='task-1', text='Задание', difficulty=2)

        rows = service.build_task_score_rows(
            variant_tasks=[ReviewVariantTaskRef(task=task, weight=3)],
            existing_scores={
                'task-1': {
                    'points': 2,
                    'max_points': 3,
                    'comment': 'Верно',
                }
            },
        )

        self.assertEqual(rows[0].task, task)
        self.assertEqual(rows[0].number, 1)
        self.assertEqual(rows[0].points, 2)
        self.assertEqual(rows[0].max_points, 3)
        self.assertEqual(rows[0].comment, 'Верно')

    def test_build_navigation_returns_neighbors_and_progress(self):
        service = ReviewService()
        event = ReviewEventRef(pk='event-1', name='КР')
        participations = [
            ReviewParticipationRef(
                pk='p1',
                student=ReviewStudentRef(pk='s1', last_name='А', first_name='А'),
                event=event,
            ),
            ReviewParticipationRef(
                pk='p2',
                student=ReviewStudentRef(pk='s2', last_name='Б', first_name='Б'),
                event=event,
            ),
            ReviewParticipationRef(
                pk='p3',
                student=ReviewStudentRef(pk='s3', last_name='В', first_name='В'),
                event=event,
            ),
        ]

        nav = service.build_navigation(participations, 'p2')

        self.assertEqual(nav.previous_participation.pk, 'p1')
        self.assertEqual(nav.next_participation.pk, 'p3')
        self.assertEqual(nav.current_position, 2)
        self.assertEqual(nav.total_positions, 3)
        self.assertEqual(nav.navigation_progress, 66.7)
