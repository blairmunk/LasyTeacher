from types import SimpleNamespace
from unittest import TestCase

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_DEMO,
    TASK_RENDER_MODE_TASK_ONLY,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
from infrastructure.services.task_document_payloads import (
    variant_task_snapshot_data,
)


class VariantTaskSnapshotDataTests(TestCase):
    def test_reads_content_decisions_frozen_on_variant_task(self):
        variant_task = SimpleNamespace(
            source_selection_id='selection-demo',
            content_order=20,
            bank_role=TASK_BANK_ROLE_DEMO,
            render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
            is_assessable=False,
            blank_cells_after=True,
            blank_cells_rows=9,
        )

        data = variant_task_snapshot_data(variant_task)

        self.assertEqual(
            data,
            {
                'source_selection_id': 'selection-demo',
                'content_order': 20,
                'bank_role': TASK_BANK_ROLE_DEMO,
                'render_mode': TASK_RENDER_MODE_WITH_FULL_SOLUTION,
                'is_assessable': False,
                'blank_cells_after': True,
                'blank_cells_rows': 9,
            },
        )

    def test_supplies_legacy_defaults_without_inventing_print_rules(self):
        data = variant_task_snapshot_data(SimpleNamespace())

        self.assertEqual(
            data,
            {
                'source_selection_id': '',
                'content_order': 0,
                'bank_role': TASK_BANK_ROLE_CONTROL,
                'render_mode': TASK_RENDER_MODE_TASK_ONLY,
                'is_assessable': True,
                'blank_cells_after': False,
                'blank_cells_rows': DEFAULT_BLANK_CELLS_ROWS,
            },
        )
