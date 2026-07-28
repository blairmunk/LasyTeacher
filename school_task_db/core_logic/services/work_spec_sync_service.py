"""Build a work specification sync plan from variant group snapshots."""

from typing import Tuple

from core_logic.entities.work_spec_sync import WorkSpecSyncItem


class WorkSpecSyncService:
    def build_plan(self, variant_group_ids) -> Tuple[WorkSpecSyncItem, ...]:
        maximum_counts = {}
        for group_ids in variant_group_ids:
            variant_counts = {}
            for group_id in group_ids:
                normalized_group_id = str(group_id)
                variant_counts[normalized_group_id] = (
                    variant_counts.get(normalized_group_id, 0) + 1
                )
            for group_id, count in variant_counts.items():
                maximum_counts[group_id] = max(
                    maximum_counts.get(group_id, 0),
                    count,
                )

        return tuple(
            WorkSpecSyncItem(
                analog_group_id=group_id,
                count=count,
                order=order,
            )
            for order, (group_id, count) in enumerate(
                maximum_counts.items(),
                start=1,
            )
        )
