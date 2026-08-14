from types import SimpleNamespace
from unittest import TestCase

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_SPACE_AREA_CM2,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_DEMO,
    TASK_RENDER_MODE_TASK_ONLY,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
from core_logic.value_objects.variant_content_snapshot import (
    variant_task_content_decisions,
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
            blank_space_area_cm2=60,
            page_break_after=True,
        )

        data = variant_task_content_decisions(variant_task)

        self.assertEqual(
            data,
            {
                'source_selection_id': 'selection-demo',
                'content_order': 20,
                'bank_role': TASK_BANK_ROLE_DEMO,
                'render_mode': TASK_RENDER_MODE_WITH_FULL_SOLUTION,
                'is_assessable': False,
                'blank_cells_after': True,
                'blank_space_area_cm2': 60,
                'page_break_after': True,
            },
        )

    def test_supplies_legacy_defaults_without_inventing_print_rules(self):
        data = variant_task_content_decisions(SimpleNamespace())

        self.assertEqual(
            data,
            {
                'source_selection_id': '',
                'content_order': 0,
                'bank_role': TASK_BANK_ROLE_CONTROL,
                'render_mode': TASK_RENDER_MODE_TASK_ONLY,
                'is_assessable': True,
                'blank_cells_after': False,
                'blank_space_area_cm2': DEFAULT_BLANK_SPACE_AREA_CM2,
                'page_break_after': False,
            },
        )
