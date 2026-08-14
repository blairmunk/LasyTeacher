"""Shared Django persistence for immutable variant content plans."""

from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
from tasks.models import Task
from works.models import (
    Variant,
    VariantContentBlockSnapshot,
    VariantTask,
)


def persist_variant_content(variant: Variant, plan) -> None:
    tasks = Task.objects.filter(
        pk__in={task_plan.task_id for task_plan in plan.tasks},
    ).select_related(
        'topic',
        'subtopic',
        'source',
    ).prefetch_related(
        'codifier_requirements__codifier',
        'codifier_content_entries__codifier',
        'images',
    )
    task_snapshots = build_task_content_snapshots(tasks)
    VariantTask.objects.bulk_create(
        [
            VariantTask(
                variant=variant,
                task_id=task_plan.task_id,
                task_snapshot=task_snapshots[
                    str(task_plan.task_id)
                ].to_mapping(),
                source_selection_id=task_plan.source_selection_id,
                content_order=task_plan.content_order,
                order=task_plan.order,
                max_points=task_plan.max_points,
                weight=task_plan.weight,
                bank_role=task_plan.bank_role,
                render_mode=task_plan.render_mode,
                is_assessable=task_plan.is_assessable,
                blank_cells_after=task_plan.blank_cells_after,
                blank_cells_rows=task_plan.blank_cells_rows,
                page_break_after=task_plan.page_break_after,
            )
            for task_plan in plan.tasks
        ]
    )
    VariantContentBlockSnapshot.objects.bulk_create(
        [
            VariantContentBlockSnapshot(
                variant=variant,
                source_content_id=block.source_content_id,
                content_type=block.content_type,
                order=block.order,
                title=block.title,
                content=dict(block.content),
            )
            for block in plan.content_blocks
        ]
    )
