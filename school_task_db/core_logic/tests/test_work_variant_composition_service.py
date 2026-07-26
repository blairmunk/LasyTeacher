from unittest import TestCase

from core_logic.services.work_variant_composition_service import (
    AvailableVariantTask,
    WorkVariantCompositionInput,
    WorkVariantCompositionService,
    WorkVariantSpecRow,
)
from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_DEMO,
    TASK_BANK_ROLE_PRACTICE,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)


class WorkVariantCompositionServiceTests(TestCase):
    def setUp(self):
        self.selection_requests = []
        self.service = WorkVariantCompositionService(
            task_selector=self._select_last_tasks,
        )

    def test_builds_numbered_variant_snapshots(self):
        plan = self.service.compose(
            self._composition_input(variant_counter=4),
            count=2,
        )

        self.assertEqual(
            [variant.number for variant in plan.variants],
            [5, 6],
        )
        self.assertEqual(plan.next_variant_counter, 6)
        self.assertEqual(plan.variants[0].work_name_snapshot, 'Рабочий лист')
        self.assertEqual(plan.variants[0].max_score_snapshot, 7)
        self.assertEqual(plan.variants[0].duration_snapshot, 40)

    def test_copies_specification_and_bank_roles_to_task_snapshots(self):
        plan = self.service.compose(self._composition_input(), count=1)

        demo_task, practice_task = plan.variants[0].tasks
        self.assertEqual(demo_task.task_id, 'demo-2')
        self.assertEqual(demo_task.order, 1)
        self.assertEqual(demo_task.max_points, 0)
        self.assertEqual(demo_task.weight, 4)
        self.assertEqual(demo_task.bank_role, TASK_BANK_ROLE_DEMO)
        self.assertEqual(
            demo_task.render_mode,
            TASK_RENDER_MODE_WITH_FULL_SOLUTION,
        )
        self.assertFalse(demo_task.is_assessable)
        self.assertTrue(demo_task.blank_cells_after)
        self.assertEqual(demo_task.blank_cells_rows, 9)

        self.assertEqual(practice_task.task_id, 'practice-2')
        self.assertEqual(practice_task.order, 2)
        self.assertEqual(practice_task.max_points, 3)
        self.assertEqual(practice_task.bank_role, TASK_BANK_ROLE_PRACTICE)
        self.assertTrue(practice_task.is_assessable)

    def test_selects_tasks_for_each_row_and_variant(self):
        self.service.compose(self._composition_input(), count=2)

        self.assertEqual(
            self.selection_requests,
            [
                (('demo-1', 'demo-2'), 1),
                (('practice-1', 'practice-2'), 1),
                (('demo-1', 'demo-2'), 1),
                (('practice-1', 'practice-2'), 1),
            ],
        )

    def test_uses_all_available_tasks_when_requested_count_is_larger(self):
        composition_input = WorkVariantCompositionInput(
            work_name='Неполная работа',
            duration=45,
            max_score=0,
            effective_max_score=4,
            variant_counter=0,
            spec_rows=(
                WorkVariantSpecRow(
                    spec_row_id='row-1',
                    count=2,
                    weight=4,
                    available_tasks=(AvailableVariantTask('task-1'),),
                ),
            ),
        )

        plan = self.service.compose(composition_input, count=1)

        self.assertEqual(
            [task.task_id for task in plan.variants[0].tasks],
            ['task-1'],
        )
        self.assertEqual(self.selection_requests, [])

    def test_rejects_non_positive_variant_count(self):
        with self.assertRaisesRegex(ValueError, 'count must be positive'):
            self.service.compose(self._composition_input(), count=0)

    def _composition_input(self, variant_counter=0):
        return WorkVariantCompositionInput(
            work_name='Рабочий лист',
            duration=40,
            max_score=0,
            effective_max_score=7,
            variant_counter=variant_counter,
            spec_rows=(
                WorkVariantSpecRow(
                    spec_row_id='demo-row',
                    count=1,
                    weight=4,
                    available_tasks=(
                        AvailableVariantTask(
                            'demo-1',
                            bank_role=TASK_BANK_ROLE_DEMO,
                        ),
                        AvailableVariantTask(
                            'demo-2',
                            bank_role=TASK_BANK_ROLE_DEMO,
                        ),
                    ),
                    render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
                    is_assessable=False,
                    blank_cells_after=True,
                    blank_cells_rows=9,
                ),
                WorkVariantSpecRow(
                    spec_row_id='practice-row',
                    count=1,
                    weight=3,
                    available_tasks=(
                        AvailableVariantTask(
                            'practice-1',
                            bank_role=TASK_BANK_ROLE_PRACTICE,
                        ),
                        AvailableVariantTask(
                            'practice-2',
                            bank_role=TASK_BANK_ROLE_PRACTICE,
                        ),
                    ),
                ),
            ),
        )

    def _select_last_tasks(self, tasks, count):
        self.selection_requests.append(
            (tuple(task.task_id for task in tasks), count),
        )
        return tuple(tasks[-count:])
