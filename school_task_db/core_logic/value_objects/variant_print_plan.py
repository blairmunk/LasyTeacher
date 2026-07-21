"""Value objects for printing variant task blocks."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple


TASK_BANK_ROLE_ANY = 'any'
TASK_BANK_ROLE_DEMO = 'demo'
TASK_BANK_ROLE_PRACTICE = 'practice'
TASK_BANK_ROLE_CONTROL = 'control'
TASK_BANK_ROLE_REMEDIAL = 'remedial'

TASK_BANK_ROLES = frozenset(
    (
        TASK_BANK_ROLE_ANY,
        TASK_BANK_ROLE_DEMO,
        TASK_BANK_ROLE_PRACTICE,
        TASK_BANK_ROLE_CONTROL,
        TASK_BANK_ROLE_REMEDIAL,
    )
)
TASK_BANK_SPECIFIC_ROLES = frozenset(
    role for role in TASK_BANK_ROLES if role != TASK_BANK_ROLE_ANY
)

TASK_BANK_ROLE_LABELS = {
    TASK_BANK_ROLE_ANY: 'Любая роль',
    TASK_BANK_ROLE_DEMO: 'Демонстрационное',
    TASK_BANK_ROLE_PRACTICE: 'Для самостоятельной работы',
    TASK_BANK_ROLE_CONTROL: 'Контрольное',
    TASK_BANK_ROLE_REMEDIAL: 'Работа над ошибками',
}

TASK_BANK_ROLE_CHOICES = tuple(TASK_BANK_ROLE_LABELS.items())
TASK_BANK_ROLE_SPECIFIC_CHOICES = tuple(
    (role, label)
    for role, label in TASK_BANK_ROLE_CHOICES
    if role != TASK_BANK_ROLE_ANY
)

TASK_RENDER_MODE_TASK_ONLY = 'task_only'
TASK_RENDER_MODE_WITH_ANSWER = 'with_answer'
TASK_RENDER_MODE_WITH_SHORT_SOLUTION = 'with_short_solution'
TASK_RENDER_MODE_WITH_FULL_SOLUTION = 'with_full_solution'

TASK_RENDER_MODES = frozenset(
    (
        TASK_RENDER_MODE_TASK_ONLY,
        TASK_RENDER_MODE_WITH_ANSWER,
        TASK_RENDER_MODE_WITH_SHORT_SOLUTION,
        TASK_RENDER_MODE_WITH_FULL_SOLUTION,
    )
)

TASK_RENDER_MODE_LABELS = {
    TASK_RENDER_MODE_TASK_ONLY: 'Только задание',
    TASK_RENDER_MODE_WITH_ANSWER: 'Задание + ответ',
    TASK_RENDER_MODE_WITH_SHORT_SOLUTION: 'Задание + краткое решение',
    TASK_RENDER_MODE_WITH_FULL_SOLUTION: 'Задание + полное решение',
}

TASK_RENDER_MODE_CHOICES = tuple(TASK_RENDER_MODE_LABELS.items())

VARIANT_PRINT_BLOCK_TASK = 'task'
VARIANT_PRINT_BLOCK_BLANK_CELLS = 'blank_cells'

VARIANT_PRINT_BLOCK_TYPES = frozenset(
    (
        VARIANT_PRINT_BLOCK_TASK,
        VARIANT_PRINT_BLOCK_BLANK_CELLS,
    )
)

DEFAULT_BLANK_CELLS_ROWS = 6
DEFAULT_BLANK_CELLS_COLUMNS = 24
DEFAULT_BLANK_CELLS_ROW_HEIGHT = 24


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


@dataclass(frozen=True)
class VariantTaskPrintRow:
    """Snapshot row used to build a printable variant plan."""

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
    blocks = []
    for row in sorted(task_rows, key=lambda item: item.order):
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
    return VariantPrintPlan(variant_id=variant_id, blocks=blocks)


def validate_task_bank_role(role: str) -> None:
    if role not in TASK_BANK_ROLES:
        raise ValueError(f'Unsupported task bank role: {role}')


def validate_task_specific_bank_role(role: str) -> None:
    if role not in TASK_BANK_SPECIFIC_ROLES:
        raise ValueError(f'Unsupported specific task bank role: {role}')


def validate_task_render_mode(render_mode: str) -> None:
    if render_mode not in TASK_RENDER_MODES:
        raise ValueError(f'Unsupported task render mode: {render_mode}')
