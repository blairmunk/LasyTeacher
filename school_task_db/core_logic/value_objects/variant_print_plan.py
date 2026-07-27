"""Value objects for printing variant task blocks."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

from core_logic.value_objects.task_print_settings import (
    validate_task_render_mode,
    validate_task_specific_bank_role,
)
from core_logic.value_objects.variant_content_snapshot import (
    VariantContentBlockItem,
    VariantContentItem,
    VariantContentSnapshot,
)

VARIANT_PRINT_BLOCK_TASK = 'task'
VARIANT_PRINT_BLOCK_BLANK_CELLS = 'blank_cells'
VARIANT_PRINT_BLOCK_THEORY = 'theory'
VARIANT_PRINT_BLOCK_TEXT = 'text'

VARIANT_PRINT_BLOCK_TYPES = frozenset(
    (
        VARIANT_PRINT_BLOCK_TASK,
        VARIANT_PRINT_BLOCK_BLANK_CELLS,
        VARIANT_PRINT_BLOCK_THEORY,
        VARIANT_PRINT_BLOCK_TEXT,
    )
)

@dataclass(frozen=True)
class VariantPrintProfile:
    """Presentation rules applied to a variant content snapshot."""

    hidden_roles: Tuple[str, ...] = field(default_factory=tuple)
    render_modes_by_role: Mapping[str, str] = field(default_factory=dict)
    blank_cells_by_role: Mapping[str, Mapping[str, Any] | bool | int] = (
        field(default_factory=dict)
    )
    hidden_content_types: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        hidden_roles = tuple(self.hidden_roles)
        render_modes_by_role = dict(self.render_modes_by_role)
        blank_cells_by_role = dict(self.blank_cells_by_role)
        hidden_content_types = tuple(self.hidden_content_types)
        for role in hidden_roles:
            validate_task_specific_bank_role(role)
        for role, render_mode in render_modes_by_role.items():
            validate_task_specific_bank_role(role)
            validate_task_render_mode(render_mode)
        for role in blank_cells_by_role:
            validate_task_specific_bank_role(role)
        object.__setattr__(self, 'hidden_roles', hidden_roles)
        object.__setattr__(self, 'render_modes_by_role', render_modes_by_role)
        object.__setattr__(self, 'blank_cells_by_role', blank_cells_by_role)
        object.__setattr__(
            self,
            'hidden_content_types',
            hidden_content_types,
        )

    def task_render_mode(self, item: VariantContentItem) -> str:
        return self.render_modes_by_role.get(item.bank_role, item.render_mode)

    def blank_cells_options(self, item: VariantContentItem) -> Mapping[str, Any]:
        if item.bank_role in self.blank_cells_by_role:
            return _blank_cells_override_options(
                self.blank_cells_by_role[item.bank_role],
                default_rows=item.blank_cells_rows,
            )
        if not item.blank_cells_after:
            return {}
        return {'rows': item.blank_cells_rows}

    def includes_item(self, item: VariantContentItem) -> bool:
        return item.bank_role not in self.hidden_roles

    def includes_content_block(self, block: VariantContentBlockItem) -> bool:
        return block.content_type not in self.hidden_content_types


@dataclass(frozen=True)
class VariantPrintBlock:
    block_type: str
    variant_task_id: str = ''
    task_id: str = ''
    source_selection_id: str = ''
    snapshot_id: str = ''
    source_content_id: str = ''
    order: int = 0
    content_order: int = 0
    content_role: str = ''
    title: str = ''
    content: Mapping[str, Any] = field(default_factory=dict)
    source_render_mode: str = ''
    render_mode: str = ''
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.block_type not in VARIANT_PRINT_BLOCK_TYPES:
            raise ValueError(f'Unsupported variant print block: {self.block_type}')
        object.__setattr__(self, 'options', dict(self.options))
        object.__setattr__(self, 'content', dict(self.content))


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


def build_variant_print_plan_from_snapshot(
    content_snapshot: VariantContentSnapshot,
    profile: VariantPrintProfile | None = None,
) -> VariantPrintPlan:
    profile = profile or VariantPrintProfile()
    ordered_block_groups = []
    for row in content_snapshot.items:
        if not profile.includes_item(row):
            continue
        task_blocks = [_task_print_block(row, profile)]
        blank_cells_options = profile.blank_cells_options(row)
        if blank_cells_options:
            task_blocks.append(
                VariantPrintBlock(
                    block_type=VARIANT_PRINT_BLOCK_BLANK_CELLS,
                    variant_task_id=row.variant_task_id,
                    task_id=row.task_id,
                    source_selection_id=row.source_selection_id,
                    order=row.order,
                    content_order=_task_content_order(row),
                    content_role=row.bank_role,
                    options=blank_cells_options,
                )
            )
        ordered_block_groups.append(
            (
                _task_content_order(row),
                row.order,
                task_blocks,
            )
        )
    for block in content_snapshot.content_blocks:
        if not profile.includes_content_block(block):
            continue
        ordered_block_groups.append(
            (
                block.order,
                0,
                [
                    VariantPrintBlock(
                        block_type=block.content_type,
                        snapshot_id=block.snapshot_id,
                        source_content_id=block.source_content_id,
                        order=block.order,
                        content_order=block.order,
                        title=block.title,
                        content=block.content,
                    ),
                ],
            )
        )
    ordered_block_groups.sort(key=lambda group: (group[0], group[1]))
    return VariantPrintPlan(
        variant_id=content_snapshot.variant_id,
        blocks=tuple(
            block
            for _, _, group in ordered_block_groups
            for block in group
        ),
    )


def _task_print_block(
    row: VariantContentItem,
    profile: VariantPrintProfile,
) -> VariantPrintBlock:
    render_mode = profile.task_render_mode(row)
    return VariantPrintBlock(
        block_type=VARIANT_PRINT_BLOCK_TASK,
        variant_task_id=row.variant_task_id,
        task_id=row.task_id,
        source_selection_id=row.source_selection_id,
        order=row.order,
        content_order=_task_content_order(row),
        content_role=row.bank_role,
        source_render_mode=row.render_mode,
        render_mode=render_mode,
        options={
            'bank_role': row.bank_role,
            'render_mode': render_mode,
            'is_assessable': row.is_assessable,
            'max_points': row.max_points,
        },
    )


def build_variant_print_profile_from_options(options) -> VariantPrintProfile:
    options = dict(options or {})
    return VariantPrintProfile(
        hidden_roles=_tuple_option(options.get('hidden_roles')),
        render_modes_by_role=_mapping_option(options.get('role_render_modes')),
        blank_cells_by_role=_mapping_option(options.get('role_blank_cells')),
        hidden_content_types=_tuple_option(
            options.get('hidden_content_types'),
        ),
    )


def _task_content_order(row: VariantContentItem) -> int:
    return row.content_order or row.order


def _tuple_option(value) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(
            item.strip()
            for item in value.split(',')
            if item.strip()
        )
    return tuple(value)


def _mapping_option(value) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _blank_cells_override_options(value, default_rows: int) -> Mapping[str, Any]:
    if value is False or value is None:
        return {}
    if value is True:
        return {'rows': default_rows}
    if isinstance(value, int):
        if value < 1:
            return {}
        return {'rows': value}
    if not isinstance(value, Mapping):
        return {}

    enabled = value.get('enabled', True)
    if enabled is False:
        return {}
    rows = value.get('rows', default_rows)
    try:
        rows = int(rows)
    except (TypeError, ValueError):
        rows = default_rows
    if rows < 1:
        return {}
    return {
        **dict(value),
        'rows': rows,
    }
