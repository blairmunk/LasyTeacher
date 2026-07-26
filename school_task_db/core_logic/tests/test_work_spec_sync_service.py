from unittest import TestCase

from core_logic.services.work_spec_sync_service import WorkSpecSyncService


class WorkSpecSyncServiceTests(TestCase):
    def setUp(self):
        self.service = WorkSpecSyncService()

    def test_uses_maximum_group_count_across_variants(self):
        plan = self.service.build_plan(
            variant_group_ids=(
                ('group-1', 'group-1', 'group-2'),
                ('group-1', 'group-2', 'group-2', 'group-2'),
            ),
        )

        self.assertEqual(
            [
                (item.analog_group_id, item.count, item.order)
                for item in plan
            ],
            [
                ('group-1', 2, 1),
                ('group-2', 3, 2),
            ],
        )

    def test_counts_task_membership_in_each_analog_group(self):
        plan = self.service.build_plan(
            variant_group_ids=(
                ('group-1', 'group-2'),
            ),
        )

        self.assertEqual(
            [item.analog_group_id for item in plan],
            ['group-1', 'group-2'],
        )

    def test_preserves_first_seen_group_order(self):
        plan = self.service.build_plan(
            variant_group_ids=(
                ('group-2', 'group-1'),
                ('group-3', 'group-1'),
            ),
        )

        self.assertEqual(
            [item.analog_group_id for item in plan],
            ['group-2', 'group-1', 'group-3'],
        )

    def test_returns_empty_plan_without_group_memberships(self):
        self.assertEqual(
            self.service.build_plan(((), ())),
            (),
        )
