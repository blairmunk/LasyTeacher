from unittest import TestCase

from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_DEMO,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
from core_logic.value_objects.work_specification import WorkTaskRoleSpec


class WorkTaskRoleSpecTests(TestCase):
    def test_accepts_demo_spec_row_for_same_analog_group_use_case(self):
        spec = WorkTaskRoleSpec(
            analog_group_id='group-1',
            count=2,
            bank_role_filter=TASK_BANK_ROLE_DEMO,
            render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
            is_assessable=False,
        )

        self.assertEqual(spec.analog_group_id, 'group-1')
        self.assertEqual(spec.count, 2)
        self.assertEqual(spec.bank_role_filter, TASK_BANK_ROLE_DEMO)
        self.assertEqual(spec.render_mode, TASK_RENDER_MODE_WITH_FULL_SOLUTION)
        self.assertFalse(spec.is_assessable)

    def test_rejects_unknown_bank_role(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported task bank role'):
            WorkTaskRoleSpec(
                analog_group_id='group-1',
                count=1,
                bank_role_filter='unknown',
            )

    def test_rejects_unknown_render_mode(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported task render mode'):
            WorkTaskRoleSpec(
                analog_group_id='group-1',
                count=1,
                render_mode='unknown',
            )

    def test_accepts_any_as_spec_filter_only(self):
        spec = WorkTaskRoleSpec(
            analog_group_id='group-1',
            count=1,
            bank_role_filter=TASK_BANK_ROLE_ANY,
        )

        self.assertEqual(spec.bank_role_filter, TASK_BANK_ROLE_ANY)

    def test_rejects_non_positive_blank_cells_rows(self):
        with self.assertRaisesRegex(ValueError, 'blank_cells_rows must be positive'):
            WorkTaskRoleSpec(
                analog_group_id='group-1',
                count=1,
                blank_cells_rows=0,
            )
