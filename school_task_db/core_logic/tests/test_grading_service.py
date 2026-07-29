from unittest import TestCase

from core_logic.entities.review import ReviewTaskRef, ReviewVariantTaskRef
from core_logic.services.grading_service import GradingService


class GradingServiceTests(TestCase):
    def test_checked_by_name_prefers_display_name_then_username_then_default(self):
        service = GradingService()

        self.assertEqual(service.checked_by_name('Иван Иванов', 'ivan'), 'Иван Иванов')
        self.assertEqual(service.checked_by_name('', 'ivan'), 'ivan')
        self.assertEqual(service.checked_by_name('', ''), 'Учитель')

    def test_next_event_status_matches_review_progress(self):
        service = GradingService()

        self.assertEqual(service.next_event_status('completed', 2, 1), 'reviewing')
        self.assertEqual(service.next_event_status('reviewing', 2, 1), 'reviewing')
        self.assertEqual(service.next_event_status('completed', 2, 2), 'graded')
        self.assertEqual(service.next_event_status('planned', 0, 0), 'reviewing')

    def test_normalize_task_scores_supports_legacy_task_keys(self):
        result = GradingService().normalize_task_scores(
            variant_tasks=[
                ReviewVariantTaskRef(
                    task=ReviewTaskRef(id='task-1', text='Задание'),
                    weight=4,
                ),
            ],
            submitted_scores={
                'task-1': {
                    'points': '3',
                    'max_points': 100,
                    'comment': 'Верно',
                },
            },
        )

        self.assertEqual(result.points, 3)
        self.assertEqual(result.max_points, 4)
        self.assertEqual(
            result.task_scores,
            {
                'task-1': {
                    'task_id': 'task-1',
                    'points': 3,
                    'max_points': 4,
                    'comment': 'Верно',
                },
            },
        )
