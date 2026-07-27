from unittest import TestCase

from core_logic.value_objects.variant_content_snapshot import (
    VariantContentBlockItem,
    VariantContentItem,
    build_variant_content_snapshot,
)
from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_DEMO,
    TASK_BANK_ROLE_PRACTICE,
    TASK_RENDER_MODE_TASK_ONLY,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
from core_logic.value_objects.variant_print_plan import (
    VARIANT_PRINT_BLOCK_BLANK_CELLS,
    VARIANT_PRINT_BLOCK_TASK,
    VARIANT_PRINT_BLOCK_TEXT,
    VARIANT_PRINT_BLOCK_THEORY,
    build_variant_print_profile_from_options,
    build_variant_print_plan_from_snapshot,
)


class VariantPrintPlanTests(TestCase):
    def test_orders_task_and_static_content_blocks_by_pedagogical_order(self):
        snapshot = build_variant_content_snapshot(
            variant_id='variant-1',
            items=[
                VariantContentItem(
                    variant_task_id='vt-practice',
                    task_id='task-practice',
                    source_selection_id='selection-practice',
                    content_order=30,
                    order=2,
                ),
                VariantContentItem(
                    variant_task_id='vt-demo',
                    task_id='task-demo',
                    source_selection_id='selection-demo',
                    content_order=10,
                    order=1,
                ),
            ],
            content_blocks=[
                VariantContentBlockItem(
                    snapshot_id='snapshot-text',
                    source_content_id='content-text',
                    content_type='text',
                    order=20,
                    title='Инструкция',
                    content={'body': 'Решите самостоятельно.'},
                ),
                VariantContentBlockItem(
                    snapshot_id='snapshot-theory',
                    source_content_id='content-theory',
                    content_type='theory',
                    order=5,
                    title='Теория',
                    content={'topics': [{'name': 'Динамика'}]},
                ),
            ],
        )

        plan = build_variant_print_plan_from_snapshot(snapshot)

        self.assertEqual(
            [block.block_type for block in plan.blocks],
            [
                VARIANT_PRINT_BLOCK_THEORY,
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_TEXT,
                VARIANT_PRINT_BLOCK_TASK,
            ],
        )
        self.assertEqual(
            [block.content_order for block in plan.blocks],
            [5, 10, 20, 30],
        )
        self.assertEqual(plan.blocks[0].title, 'Теория')
        self.assertEqual(
            plan.blocks[2].content,
            {'body': 'Решите самостоятельно.'},
        )

    def test_print_profile_can_hide_static_content_types(self):
        snapshot = build_variant_content_snapshot(
            variant_id='variant-1',
            items=[],
            content_blocks=[
                VariantContentBlockItem(
                    snapshot_id='snapshot-theory',
                    source_content_id='content-theory',
                    content_type='theory',
                    order=5,
                ),
                VariantContentBlockItem(
                    snapshot_id='snapshot-text',
                    source_content_id='content-text',
                    content_type='text',
                    order=10,
                ),
            ],
        )
        profile = build_variant_print_profile_from_options({
            'hidden_content_types': 'theory',
        })

        plan = build_variant_print_plan_from_snapshot(snapshot, profile)

        self.assertEqual(
            [block.block_type for block in plan.blocks],
            [VARIANT_PRINT_BLOCK_TEXT],
        )

    def test_builds_content_snapshot_from_variant_snapshot_rows(self):
        snapshot = build_variant_content_snapshot(
            variant_id='variant-1',
            items=[
                VariantContentItem(
                    variant_task_id='vt-2',
                    task_id='task-2',
                    order=2,
                    source_selection_id='selection-practice',
                    bank_role=TASK_BANK_ROLE_PRACTICE,
                    render_mode=TASK_RENDER_MODE_TASK_ONLY,
                    is_assessable=True,
                    max_points=3,
                    blank_cells_after=True,
                    blank_cells_rows=8,
                ),
                VariantContentItem(
                    variant_task_id='vt-1',
                    task_id='task-1',
                    order=1,
                    source_selection_id='selection-demo',
                    bank_role=TASK_BANK_ROLE_DEMO,
                    render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
                    is_assessable=False,
                    max_points=0,
                ),
            ],
        )

        self.assertEqual(snapshot.variant_id, 'variant-1')
        self.assertEqual(
            [item.variant_task_id for item in snapshot.items],
            ['vt-1', 'vt-2'],
        )
        self.assertEqual(snapshot.assessable_variant_task_ids, ('vt-2',))

    def test_builds_print_blocks_from_content_snapshot(self):
        content_snapshot = build_variant_content_snapshot(
            variant_id='variant-1',
            items=[
                VariantContentItem(
                    variant_task_id='vt-2',
                    task_id='task-2',
                    order=2,
                    source_selection_id='selection-practice',
                    bank_role=TASK_BANK_ROLE_PRACTICE,
                    render_mode=TASK_RENDER_MODE_TASK_ONLY,
                    is_assessable=True,
                    max_points=3,
                    blank_cells_after=True,
                    blank_cells_rows=8,
                ),
                VariantContentItem(
                    variant_task_id='vt-1',
                    task_id='task-1',
                    order=1,
                    source_selection_id='selection-demo',
                    bank_role=TASK_BANK_ROLE_DEMO,
                    render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
                    is_assessable=False,
                    max_points=0,
                ),
            ],
        )

        plan = build_variant_print_plan_from_snapshot(content_snapshot)

        self.assertEqual(plan.variant_id, 'variant-1')
        self.assertEqual(
            [block.block_type for block in plan.blocks],
            [
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_BLANK_CELLS,
            ],
        )
        self.assertEqual(
            [block.variant_task_id for block in plan.task_blocks],
            ['vt-1', 'vt-2'],
        )
        self.assertEqual(plan.assessable_variant_task_ids, ('vt-2',))
        self.assertEqual(
            plan.blocks[0].options['render_mode'],
            TASK_RENDER_MODE_WITH_FULL_SOLUTION,
        )
        self.assertEqual(plan.blocks[0].content_role, TASK_BANK_ROLE_DEMO)
        self.assertEqual(
            plan.blocks[0].source_render_mode,
            TASK_RENDER_MODE_WITH_FULL_SOLUTION,
        )
        self.assertEqual(
            plan.blocks[0].render_mode,
            TASK_RENDER_MODE_WITH_FULL_SOLUTION,
        )
        self.assertEqual(
            plan.blocks[0].source_selection_id,
            'selection-demo',
        )
        self.assertFalse(plan.blocks[0].options['is_assessable'])
        self.assertEqual(
            plan.blocks[2].source_selection_id,
            'selection-practice',
        )
        self.assertEqual(plan.blocks[2].options, {'rows': 8})

    def test_print_profile_overrides_rendering_without_changing_content(self):
        content_snapshot = build_variant_content_snapshot(
            variant_id='variant-1',
            items=[
                VariantContentItem(
                    variant_task_id='vt-1',
                    task_id='task-1',
                    order=1,
                    bank_role=TASK_BANK_ROLE_DEMO,
                    render_mode=TASK_RENDER_MODE_TASK_ONLY,
                    is_assessable=False,
                ),
                VariantContentItem(
                    variant_task_id='vt-2',
                    task_id='task-2',
                    order=2,
                    bank_role=TASK_BANK_ROLE_PRACTICE,
                    render_mode=TASK_RENDER_MODE_TASK_ONLY,
                    blank_cells_after=False,
                ),
            ],
        )
        profile = build_variant_print_profile_from_options({
            'role_render_modes': {
                TASK_BANK_ROLE_DEMO: TASK_RENDER_MODE_WITH_FULL_SOLUTION,
            },
            'role_blank_cells': {
                TASK_BANK_ROLE_PRACTICE: {'rows': 9},
            },
        })

        plan = build_variant_print_plan_from_snapshot(
            content_snapshot,
            profile=profile,
        )

        self.assertEqual(content_snapshot.assessable_variant_task_ids, ('vt-2',))
        self.assertEqual(
            [block.block_type for block in plan.blocks],
            [
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_BLANK_CELLS,
            ],
        )
        self.assertEqual(
            plan.blocks[0].options['render_mode'],
            TASK_RENDER_MODE_WITH_FULL_SOLUTION,
        )
        self.assertEqual(plan.blocks[0].content_role, TASK_BANK_ROLE_DEMO)
        self.assertEqual(
            plan.blocks[0].source_render_mode,
            TASK_RENDER_MODE_TASK_ONLY,
        )
        self.assertEqual(
            plan.blocks[0].render_mode,
            TASK_RENDER_MODE_WITH_FULL_SOLUTION,
        )
        self.assertEqual(plan.blocks[2].content_role, TASK_BANK_ROLE_PRACTICE)
        self.assertEqual(plan.blocks[2].options['rows'], 9)

    def test_print_profile_can_hide_roles(self):
        content_snapshot = build_variant_content_snapshot(
            variant_id='variant-1',
            items=[
                VariantContentItem(
                    variant_task_id='vt-1',
                    task_id='task-1',
                    order=1,
                    bank_role=TASK_BANK_ROLE_DEMO,
                    is_assessable=False,
                ),
                VariantContentItem(
                    variant_task_id='vt-2',
                    task_id='task-2',
                    order=2,
                    bank_role=TASK_BANK_ROLE_PRACTICE,
                ),
            ],
        )
        profile = build_variant_print_profile_from_options({
            'hidden_roles': TASK_BANK_ROLE_DEMO,
        })

        plan = build_variant_print_plan_from_snapshot(
            content_snapshot,
            profile=profile,
        )

        self.assertEqual(
            [block.variant_task_id for block in plan.task_blocks],
            ['vt-2'],
        )

    def test_rejects_any_role_for_concrete_variant_task_row(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported specific task bank role'):
            VariantContentItem(
                variant_task_id='vt-1',
                task_id='task-1',
                order=1,
                bank_role=TASK_BANK_ROLE_ANY,
            )

    def test_rejects_non_positive_blank_cells_rows(self):
        with self.assertRaisesRegex(ValueError, 'blank_cells_rows must be positive'):
            VariantContentItem(
                variant_task_id='vt-1',
                task_id='task-1',
                order=1,
                blank_cells_rows=0,
            )
