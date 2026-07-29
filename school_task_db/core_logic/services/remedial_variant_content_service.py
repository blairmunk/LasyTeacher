"""Build immutable task rows for a remedial variant."""

from core_logic.interfaces.work_repo import VariantTaskSnapshotParams
from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_REMEDIAL,
)


def build_remedial_variant_task_snapshots(task_ids, tasks):
    """Preserve selection order and make remedial content decisions explicit."""
    tasks_by_id = {str(task.id): task for task in tasks}
    snapshots = []
    for order, task_id in enumerate(task_ids, start=1):
        task = tasks_by_id.get(str(task_id))
        if task is None:
            continue
        max_points = task.difficulty or 1
        snapshots.append(
            VariantTaskSnapshotParams(
                task_id=str(task.id),
                order=order,
                content_order=order,
                max_points=max_points,
                bank_role=TASK_BANK_ROLE_REMEDIAL,
            )
        )
    return snapshots
