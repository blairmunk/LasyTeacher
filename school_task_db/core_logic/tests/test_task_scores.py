from unittest import TestCase

from core_logic.value_objects.task_scores import (
    normalize_task_scores,
    task_score_records_by_score_key,
    task_score_records_by_task_id,
)


class TaskScoreNormalizationTests(TestCase):
    def test_normalizes_legacy_task_id_keyed_scores(self):
        records = normalize_task_scores({
            'task-1': {
                'points': 2,
                'max_points': 3,
                'comment': 'Верно',
            },
        })

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].score_key, 'task-1')
        self.assertEqual(records[0].task_id, 'task-1')
        self.assertEqual(records[0].variant_task_id, '')
        self.assertEqual(records[0].points, 2)
        self.assertEqual(records[0].max_points, 3)
        self.assertEqual(records[0].comment, 'Верно')
        self.assertEqual(records[0].raw['points'], 2)

    def test_normalizes_variant_task_keyed_scores(self):
        records = normalize_task_scores({
            'variant-task-1': {
                'task_id': 'task-1',
                'points': 2,
                'max_points': 3,
            },
        })

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].score_key, 'variant-task-1')
        self.assertEqual(records[0].task_id, 'task-1')
        self.assertEqual(records[0].variant_task_id, 'variant-task-1')

    def test_normalizes_explicit_variant_task_id(self):
        records = normalize_task_scores({
            'task-1': {
                'task_id': 'task-1',
                'variant_task_id': 'variant-task-1',
                'points': 1,
            },
        })

        self.assertEqual(records[0].score_key, 'task-1')
        self.assertEqual(records[0].task_id, 'task-1')
        self.assertEqual(records[0].variant_task_id, 'variant-task-1')

    def test_indexes_normalized_scores(self):
        task_scores = {
            'variant-task-1': {'task_id': 'task-1', 'points': 2},
            'task-2': {'points': 1},
        }

        by_task = task_score_records_by_task_id(task_scores)
        by_score_key = task_score_records_by_score_key(task_scores)

        self.assertEqual(by_task['task-1'].score_key, 'variant-task-1')
        self.assertEqual(by_task['task-2'].score_key, 'task-2')
        self.assertEqual(by_score_key['variant-task-1'].task_id, 'task-1')

    def test_skips_invalid_scores(self):
        self.assertEqual(normalize_task_scores(None), ())
        self.assertEqual(
            normalize_task_scores({
                'task-1': 'bad',
                '': {'points': 1},
            }),
            (),
        )
