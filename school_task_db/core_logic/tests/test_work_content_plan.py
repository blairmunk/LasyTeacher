from unittest import TestCase

from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_DEMO,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
from core_logic.value_objects.work_content_plan import (
    WorkContentPlan,
    WorkOriginalMistakesBlock,
    WorkTaskSelectionBlock,
    WorkTextBlock,
    WorkTheoryBlock,
    build_work_content_plan,
    build_work_content_plan_from_task_rows,
)
from core_logic.value_objects.work_specification import (
    WorkTaskSelectionSpec,
)


class WorkContentPlanTests(TestCase):
    def test_orders_mixed_pedagogical_content(self):
        plan = WorkContentPlan(
            blocks=(
                WorkTaskSelectionBlock(
                    selection=WorkTaskSelectionSpec(
                        analog_group_id='group-1',
                        count=3,
                        order=30,
                    ),
                ),
                WorkTheoryBlock(
                    order=10,
                    title='Теория',
                    topic_ids=('topic-1',),
                ),
                WorkTextBlock(
                    order=20,
                    title='Инструкция',
                    body='Решите самостоятельно.',
                ),
                WorkOriginalMistakesBlock(
                    order=5,
                ),
            ),
        )

        self.assertEqual(
            [block.order for block in plan.blocks],
            [5, 10, 20, 30],
        )
        self.assertEqual(
            plan.task_selections[0].analog_group_id,
            'group-1',
        )

    def test_rejects_unknown_content_block(self):
        with self.assertRaises(ValueError):
            WorkContentPlan(blocks=(object(),))

    def test_builds_plan_from_existing_task_rows(self):
        analog_group = type(
            'AnalogGroup',
            (),
            {'pk': 'group-1', 'name': 'Законы Ньютона'},
        )()
        row = type(
            'TaskRow',
            (),
            {
                'analog_group': analog_group,
                'count': 2,
                'order': 7,
                'bank_role_filter': TASK_BANK_ROLE_DEMO,
                'render_mode': TASK_RENDER_MODE_WITH_FULL_SOLUTION,
                'is_assessable': False,
                'blank_cells_after': True,
                'blank_cells_rows': 8,
                'weight': 3,
            },
        )()

        plan = build_work_content_plan_from_task_rows([row])

        block = plan.task_selection_blocks[0]
        self.assertEqual(block.title, 'Законы Ньютона')
        self.assertEqual(block.selection.analog_group_id, 'group-1')
        self.assertEqual(block.selection.count, 2)
        self.assertEqual(block.selection.order, 7)
        self.assertEqual(
            block.selection.render_mode,
            TASK_RENDER_MODE_WITH_FULL_SOLUTION,
        )
        self.assertFalse(block.selection.is_assessable)
        self.assertEqual(block.selection.blank_cells_rows, 8)

    def test_builds_plan_from_persistent_content_rows(self):
        theory_row = type(
            'ContentRow',
            (),
            {
                'content_type': 'theory',
                'order': 10,
                'title': 'Основные формулы',
                'body': '',
                'topic_ids': ('topic-1',),
                'include_subtopics': True,
            },
        )()
        text_row = type(
            'ContentRow',
            (),
            {
                'content_type': 'text',
                'order': 20,
                'title': 'Инструкция',
                'body': 'Покажите ход решения.',
                'topic_ids': (),
                'include_subtopics': False,
            },
        )()

        plan = build_work_content_plan(
            content_rows=[text_row, theory_row],
        )

        theory, text = plan.blocks
        self.assertIsInstance(theory, WorkTheoryBlock)
        self.assertEqual(theory.topic_ids, ('topic-1',))
        self.assertTrue(theory.include_subtopics)
        self.assertIsInstance(text, WorkTextBlock)
        self.assertEqual(text.body, 'Покажите ход решения.')
