"""Build an immutable content plan for a remedial variant."""

from core_logic.entities.work_variant_composition import (
    VariantCreationPlan,
    VariantTaskCreationPlan,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_SPACE_AREA_CM2,
    TASK_BANK_ROLE_REMEDIAL,
    TASK_RENDER_MODE_TASK_ONLY,
)


def build_remedial_variant_creation_plan(
    *,
    task_ids,
    tasks,
    number,
    work_name,
    duration=45,
    content_blocks=(),
):
    """Preserve selection order and make remedial content decisions explicit."""
    tasks_by_id = {str(task.id): task for task in tasks}
    task_plans = []
    for order, task_id in enumerate(task_ids, start=1):
        task = tasks_by_id.get(str(task_id))
        if task is None:
            continue
        max_points = task.difficulty or 1
        task_plans.append(
            VariantTaskCreationPlan(
                task_id=str(task.id),
                source_selection_id='',
                content_order=order,
                order=order,
                max_points=max_points,
                weight=max_points,
                bank_role=TASK_BANK_ROLE_REMEDIAL,
                render_mode=TASK_RENDER_MODE_TASK_ONLY,
                is_assessable=True,
                blank_cells_after=False,
                blank_space_area_cm2=DEFAULT_BLANK_SPACE_AREA_CM2,
                page_break_after=False,
            )
        )
    return VariantCreationPlan(
        number=number,
        work_name_snapshot=work_name,
        max_score_snapshot=sum(task.max_points for task in task_plans),
        duration_snapshot=duration,
        tasks=tuple(task_plans),
        content_blocks=tuple(content_blocks),
    )
