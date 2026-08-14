from types import SimpleNamespace
from unittest import TestCase

from core_logic.value_objects.variant_content_snapshot import (
    build_variant_content_snapshot_from_sources,
)


class VariantContentSnapshotSourceTests(TestCase):
    def test_builds_ordered_snapshot_from_detached_sources(self):
        snapshot = build_variant_content_snapshot_from_sources(
            variant_id='variant-1',
            variant_tasks=[
                SimpleNamespace(
                    pk='variant-task-2',
                    task_id='task-2',
                    order=2,
                    max_points=3,
                    source_selection_id='selection-2',
                    content_order=30,
                    bank_role='practice',
                    render_mode='task_only',
                    is_assessable=True,
                    blank_cells_after=True,
                    blank_cells_rows=8,
                    page_break_after=True,
                ),
                SimpleNamespace(
                    pk='variant-task-1',
                    task_id='task-1',
                    order=1,
                    max_points=0,
                    source_selection_id='selection-1',
                    content_order=10,
                    bank_role='demo',
                    render_mode='with_full_solution',
                    is_assessable=False,
                    blank_cells_after=False,
                    blank_cells_rows=5,
                ),
            ],
            content_blocks=[
                SimpleNamespace(
                    pk='content-1',
                    source_content_id='source-content-1',
                    content_type='theory',
                    order=20,
                    title='Теория',
                    content={'topics': []},
                ),
            ],
        )

        self.assertEqual(snapshot.variant_id, 'variant-1')
        self.assertEqual(
            [item.variant_task_id for item in snapshot.items],
            ['variant-task-1', 'variant-task-2'],
        )
        self.assertFalse(snapshot.items[0].is_assessable)
        self.assertEqual(snapshot.items[1].blank_cells_rows, 8)
        self.assertTrue(snapshot.items[1].page_break_after)
        self.assertEqual(snapshot.content_blocks[0].snapshot_id, 'content-1')
        self.assertEqual(snapshot.content_blocks[0].title, 'Теория')
