from unittest import TestCase

from core_logic.services.work_score_allocation_service import (
    WorkScoreAllocationService,
    WorkScoreSpecRow,
)


class WorkScoreAllocationServiceTests(TestCase):
    def setUp(self):
        self.service = WorkScoreAllocationService()

    def test_uses_weights_as_points_without_normalization(self):
        allocations = self.service.allocate(
            max_score=0,
            spec_rows=(
                WorkScoreSpecRow('row-1', count=2, weight=3),
                WorkScoreSpecRow('row-2', count=1, weight=5),
            ),
        )

        self.assertEqual(
            [(item.spec_row_id, item.points) for item in allocations],
            [('row-1', 3), ('row-1', 3), ('row-2', 5)],
        )

    def test_normalizes_points_and_preserves_total_score(self):
        allocations = self.service.allocate(
            max_score=10,
            spec_rows=(
                WorkScoreSpecRow('row-1', count=2, weight=1),
                WorkScoreSpecRow('row-2', count=1, weight=2),
            ),
        )

        self.assertEqual(
            [(item.spec_row_id, item.points) for item in allocations],
            [('row-1', 3), ('row-1', 2), ('row-2', 5)],
        )
        self.assertEqual(sum(item.points for item in allocations), 10)

    def test_non_assessable_rows_receive_zero_points(self):
        allocations = self.service.allocate(
            max_score=7,
            spec_rows=(
                WorkScoreSpecRow(
                    'demo',
                    count=1,
                    weight=4,
                    is_assessable=False,
                ),
                WorkScoreSpecRow('practice', count=1, weight=3),
            ),
        )

        self.assertEqual(
            [(item.spec_row_id, item.points) for item in allocations],
            [('demo', 0), ('practice', 7)],
        )

    def test_returns_zeroes_when_no_rows_are_assessable(self):
        allocations = self.service.allocate(
            max_score=10,
            spec_rows=(
                WorkScoreSpecRow(
                    'demo',
                    count=2,
                    weight=4,
                    is_assessable=False,
                ),
            ),
        )

        self.assertEqual([item.points for item in allocations], [0, 0])

    def test_returns_empty_allocation_without_spec_rows(self):
        self.assertEqual(self.service.allocate(max_score=10, spec_rows=()), ())

    def test_validates_spec_rows(self):
        with self.assertRaisesRegex(ValueError, 'spec_row_id is required'):
            WorkScoreSpecRow('', count=1, weight=1)
        with self.assertRaisesRegex(ValueError, 'count must be positive'):
            WorkScoreSpecRow('row-1', count=0, weight=1)
        with self.assertRaisesRegex(ValueError, 'weight must be non-negative'):
            WorkScoreSpecRow('row-1', count=1, weight=-1)
