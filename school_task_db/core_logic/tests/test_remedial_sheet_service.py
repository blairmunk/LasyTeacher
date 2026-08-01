from unittest import TestCase

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
                variant_task_id=f'row-{index}',
                order=index,
            )
            for index in range(1, 5)
        ]
        source = RemedialSheetSource(
            variant=None,
            student=None,
            source_work=None,
            mark=None,
            task_scores={
                'row-1': {'points': 7, 'max_points': 10},
                'row-2': {'points': 2, 'max_points': 10},
                'row-3': {'points': 0, 'max_points': 10},
            },
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

    def test_build_supports_legacy_scores_keyed_by_task(self):
        source = RemedialSheetSource(
            variant=None,
            student=None,
            source_work=None,
            mark=None,
            task_scores={
                'task-1': {'points': 4, 'max_points': 5},
            },
            original_tasks=[RemedialOriginalTaskSource(
                task=RemedialTaskRef(pk='task-1', text='Задание'),
                variant_task_id='row-1',
                order=1,
            )],
        )

        result = RemedialSheetService().build(source)

        self.assertEqual(result.original_tasks[0].status, 'ok')
        self.assertEqual(result.original_tasks[0].pct, 80.0)
