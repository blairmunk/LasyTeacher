from unittest import TestCase
from decimal import Decimal

from core_logic.entities.work import (
    RemedialOriginalTaskSource,
    RemedialSheetSource,
    RemedialTaskRef,
)
from core_logic.services.remedial_sheet_service import RemedialSheetService


class RemedialSheetServiceTests(TestCase):
    def test_build_resolves_scores_and_classifies_original_tasks(self):
        tasks = [
            RemedialOriginalTaskSource(
                task=RemedialTaskRef(pk=f'task-{index}', text='Задание'),
                order=index,
                points=points,
                max_points=max_points,
            )
            for index, points, max_points in (
                (1, 7, 10),
                (2, 2, 10),
                (3, 0, 10),
                (4, None, None),
            )
        ]
        source = RemedialSheetSource(
            variant=None,
            student=None,
            source_work=None,
            mark=None,
            original_tasks=tasks,
        )

        result = RemedialSheetService().build(source)

        self.assertEqual(
            [item.status for item in result.original_tasks],
            ['ok', 'partial', 'fail', 'unknown'],
        )
        self.assertEqual(
            [item.pct for item in result.original_tasks],
            [70.0, 20.0, 0.0, 0],
        )

    def test_build_supports_decimal_snapshot_scores(self):
        source = RemedialSheetSource(
            variant=None,
            student=None,
            source_work=None,
            mark=None,
            original_tasks=[RemedialOriginalTaskSource(
                task=RemedialTaskRef(pk='task-1', text='Задание'),
                order=1,
                points=Decimal('4.00'),
                max_points=Decimal('5.00'),
            )],
        )

        result = RemedialSheetService().build(source)

        self.assertEqual(result.original_tasks[0].status, 'ok')
        self.assertEqual(result.original_tasks[0].pct, 80.0)
