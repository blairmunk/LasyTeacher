from unittest import TestCase

from core_logic.entities.student import (
    TaskResultGroupRef,
    TaskResultsSource,
    TaskResultVariantRow,
)
from core_logic.services.student_task_result_service import (
    StudentTaskResultService,
)


class StudentTaskResultServiceTests(TestCase):
    def test_build_prefers_variant_task_score_and_adds_group(self):
        source = TaskResultsSource(
            task_scores={
                'row-1': {
                    'task_id': 'task-1',
                    'points': 2,
                    'max_points': 5,
                },
                'task-1': {'points': 5, 'max_points': 5},
            },
            variant_tasks=(TaskResultVariantRow('row-1', 'task-1'),),
            groups=(TaskResultGroupRef('task-1', 'group-1', 'Динамика'),),
        )

        result = StudentTaskResultService().build(source)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].variant_task_id, 'row-1')
        self.assertEqual(result[0].points, 2)
        self.assertEqual(result[0].group_id, 'group-1')

    def test_build_normalizes_legacy_task_scores_without_variant(self):
        source = TaskResultsSource(task_scores={
            'task-1': {'points': 1, 'max_points': 2},
        })

        result = StudentTaskResultService().build(source)

        self.assertEqual(result[0].task_id, 'task-1')
        self.assertEqual(result[0].variant_task_id, '')
        self.assertEqual(result[0].points, 1)
        self.assertIsNone(result[0].group_id)
