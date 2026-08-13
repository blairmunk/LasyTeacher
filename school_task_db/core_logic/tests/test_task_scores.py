from unittest import TestCase

from core_logic.value_objects.task_scores import (
    TaskScoreRecord,
    normalize_task_scores,
    resolve_normalized_task_score_record,
    resolve_task_score_record,
    task_score_records_for_attempt,
    task_score_records_by_score_key,
    task_score_records_by_task_id,
    task_score_records_by_variant_task_id,
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
        self.assertEqual(records[0].points, 2.0)
        self.assertEqual(records[0].max_points, 3.0)
        self.assertEqual(records[0].comment, 'Верно')

    def test_normalizes_numeric_strings_and_discards_invalid_numbers(self):
        records = normalize_task_scores({
            'task-1': {'points': '2.5', 'max_points': 'bad'},
        })

        self.assertEqual(records[0].points, 2.5)
        self.assertIsNone(records[0].max_points)

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

    def test_attempt_records_keep_repeated_task_in_distinct_snapshot_slots(self):
        records = task_score_records_for_attempt({
            'variant-task-1': {'task_id': 'task-1', 'points': 1},
            'variant-task-2': {'task_id': 'task-1', 'points': 2},
        })

        self.assertEqual(
            [record.variant_task_id for record in records],
            ['variant-task-1', 'variant-task-2'],
        )

    def test_attempt_records_prefer_snapshot_score_over_legacy_duplicate(self):
        records = task_score_records_for_attempt({
            'task-1': {'points': 1},
            'variant-task-1': {'task_id': 'task-1', 'points': 2},
        })

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].variant_task_id, 'variant-task-1')
        self.assertEqual(records[0].points, 2)

    def test_attempt_records_deduplicate_repeated_snapshot_identity(self):
        records = task_score_records_for_attempt({
            'score-1': {
                'task_id': 'task-1',
                'variant_task_id': 'variant-task-1',
                'points': 1,
            },
            'score-2': {
                'task_id': 'task-1',
                'variant_task_id': 'variant-task-1',
                'points': 2,
            },
        })

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].points, 1)

    def test_indexes_normalized_scores(self):
        task_scores = {
            'variant-task-1': {'task_id': 'task-1', 'points': 2},
            'task-2': {'points': 1},
        }

        by_task = task_score_records_by_task_id(task_scores)
        by_score_key = task_score_records_by_score_key(task_scores)
        by_variant_task = task_score_records_by_variant_task_id(task_scores)

        self.assertEqual(by_task['task-1'].score_key, 'variant-task-1')
        self.assertEqual(by_task['task-2'].score_key, 'task-2')
        self.assertEqual(by_score_key['variant-task-1'].task_id, 'task-1')
        self.assertEqual(
            by_variant_task['variant-task-1'].task_id,
            'task-1',
        )

    def test_resolves_variant_task_before_legacy_task_score(self):
        task_scores = {
            'task-1': {'points': 1},
            'variant-task-1': {
                'task_id': 'task-1',
                'points': 3,
            },
        }

        record = resolve_task_score_record(
            task_scores,
            variant_task_id='variant-task-1',
            task_id='task-1',
        )

        self.assertEqual(record.score_key, 'variant-task-1')
        self.assertEqual(record.points, 3)

    def test_resolver_falls_back_to_legacy_task_score(self):
        record = resolve_task_score_record(
            {'task-1': {'points': 2}},
            variant_task_id='missing-variant-task',
            task_id='task-1',
        )

        self.assertEqual(record.score_key, 'task-1')
        self.assertEqual(record.points, 2)

    def test_resolves_already_normalized_variant_task_score(self):
        records = (
            TaskScoreRecord('task-1', 'task-1', points=1),
            TaskScoreRecord(
                'variant-task-1',
                'task-1',
                variant_task_id='variant-task-1',
                points=3,
            ),
        )

        record = resolve_normalized_task_score_record(
            records,
            variant_task_id='variant-task-1',
            task_id='task-1',
        )

        self.assertEqual(record.score_key, 'variant-task-1')
        self.assertEqual(record.points, 3)

    def test_skips_invalid_scores(self):
        self.assertEqual(normalize_task_scores(None), ())
        self.assertEqual(
            normalize_task_scores({
                'task-1': 'bad',
                '': {'points': 1},
            }),
            (),
        )
