"""Value objects for printing variant task blocks."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_COLUMNS,
    DEFAULT_BLANK_CELLS_ROW_HEIGHT,
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_CHOICES,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_DEMO,
    TASK_BANK_ROLE_LABELS,
    TASK_BANK_ROLE_PRACTICE,
    TASK_BANK_ROLE_REMEDIAL,
    TASK_BANK_ROLE_SPECIFIC_CHOICES,
    TASK_BANK_ROLES,
    TASK_BANK_SPECIFIC_ROLES,
    TASK_RENDER_MODE_CHOICES,
    TASK_RENDER_MODE_LABELS,
    TASK_RENDER_MODE_TASK_ONLY,
    TASK_RENDER_MODE_WITH_ANSWER,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
    TASK_RENDER_MODE_WITH_SHORT_SOLUTION,
    TASK_RENDER_MODES,
    validate_task_bank_role,
    validate_task_render_mode,
    validate_task_specific_bank_role,
)
from core_logic.value_objects.variant_content_plan import (
    VariantContentItem,
    VariantContentPlan,
    build_variant_content_plan,
)

VARIANT_PRINT_BLOCK_TASK = 'task'
VARIANT_PRINT_BLOCK_BLANK_CELLS = 'blank_cells'

VARIANT_PRINT_BLOCK_TYPES = frozenset(
    (
        VARIANT_PRINT_BLOCK_TASK,
        VARIANT_PRINT_BLOCK_BLANK_CELLS,
    )
)


@dataclass(frozen=True)
class WorkTaskRoleSpec:
    """Specification row for selecting and printing tasks from a bank group."""

    analog_group_id: str
    count: int
    order: int = 0
    bank_role_filter: str = TASK_BANK_ROLE_ANY
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_cells_rows: int = DEFAULT_BLANK_CELLS_ROWS
    weight: int = 1

    def __post_init__(self):
        if not self.analog_group_id:
            raise ValueError('analog_group_id is required')
        if self.count < 1:
            raise ValueError('count must be positive')
        if self.weight < 0:
            raise ValueError('weight must be non-negative')
        if self.blank_cells_rows < 1:
            raise ValueError('blank_cells_rows must be positive')
        validate_task_bank_role(self.bank_role_filter)
        validate_task_render_mode(self.render_mode)


VariantTaskPrintRow = VariantContentItem


@dataclass(frozen=True)
class VariantPrintBlock:
    block_type: str
    variant_task_id: str = ''
    task_id: str = ''
    order: int = 0
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.block_type not in VARIANT_PRINT_BLOCK_TYPES:
            raise ValueError(f'Unsupported variant print block: {self.block_type}')
        object.__setattr__(self, 'options', dict(self.options))


@dataclass(frozen=True)
class VariantPrintPlan:
    variant_id: str
    blocks: Tuple[VariantPrintBlock, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not self.variant_id:
            raise ValueError('variant_id is required')
        object.__setattr__(self, 'blocks', tuple(self.blocks))

    @property
    def task_blocks(self) -> Tuple[VariantPrintBlock, ...]:
        return tuple(
            block
            for block in self.blocks
            if block.block_type == VARIANT_PRINT_BLOCK_TASK
        )

    @property
    def assessable_variant_task_ids(self) -> Tuple[str, ...]:
        return tuple(
            block.variant_task_id
            for block in self.task_blocks
            if block.options.get('is_assessable')
        )


def build_variant_print_plan(
    variant_id: str,
    task_rows,
) -> VariantPrintPlan:
    return build_variant_print_plan_from_content_plan(
        build_variant_content_plan(
            variant_id=variant_id,
            items=task_rows,
        )
    )


def build_variant_print_plan_from_content_plan(
    content_plan: VariantContentPlan,
) -> VariantPrintPlan:
    blocks = []
    for row in content_plan.items:
        blocks.append(
            VariantPrintBlock(
                block_type=VARIANT_PRINT_BLOCK_TASK,
                variant_task_id=row.variant_task_id,
                task_id=row.task_id,
                order=row.order,
                options={
                    'bank_role': row.bank_role,
                    'render_mode': row.render_mode,
                    'is_assessable': row.is_assessable,
                    'max_points': row.max_points,
                },
            )
        )
        if row.blank_cells_after:
            blocks.append(
                VariantPrintBlock(
                    block_type=VARIANT_PRINT_BLOCK_BLANK_CELLS,
                    variant_task_id=row.variant_task_id,
                    task_id=row.task_id,
                    order=row.order,
                    options={'rows': row.blank_cells_rows},
                )
            )
    return VariantPrintPlan(variant_id=content_plan.variant_id, blocks=blocks)
