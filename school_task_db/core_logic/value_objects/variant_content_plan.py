"""Value objects for variant content snapshots."""

from dataclasses import dataclass, field
from typing import Tuple

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_CONTROL,
    TASK_RENDER_MODE_TASK_ONLY,
    validate_task_render_mode,
    validate_task_specific_bank_role,
)


@dataclass(frozen=True)
class VariantContentItem:
    """Snapshot content item included in a concrete variant."""

    variant_task_id: str
    task_id: str
    order: int
    max_points: int = 0
    bank_role: str = TASK_BANK_ROLE_CONTROL
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_cells_rows: int = DEFAULT_BLANK_CELLS_ROWS

    def __post_init__(self):
        if not self.variant_task_id:
            raise ValueError('variant_task_id is required')
        if not self.task_id:
            raise ValueError('task_id is required')
        if self.order < 1:
            raise ValueError('order must be positive')
        if self.max_points < 0:
            raise ValueError('max_points must be non-negative')
        if self.blank_cells_rows < 1:
            raise ValueError('blank_cells_rows must be positive')
        validate_task_specific_bank_role(self.bank_role)
        validate_task_render_mode(self.render_mode)


@dataclass(frozen=True)
class VariantContentPlan:
    """Ordered content snapshot for one variant."""

    variant_id: str
    items: Tuple[VariantContentItem, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not self.variant_id:
            raise ValueError('variant_id is required')
        object.__setattr__(
            self,
            'items',
            tuple(sorted(self.items, key=lambda item: item.order)),
        )

    @property
    def assessable_variant_task_ids(self) -> Tuple[str, ...]:
        return tuple(
            item.variant_task_id
            for item in self.items
            if item.is_assessable
        )


def build_variant_content_plan(
    variant_id: str,
    items,
) -> VariantContentPlan:
    return VariantContentPlan(
        variant_id=variant_id,
        items=tuple(items),
    )
