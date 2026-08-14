"""Value objects for printing variant task blocks."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

from core_logic.value_objects.variant_content_snapshot import (
    VARIANT_STATIC_CONTENT_TYPES,
    VariantContentBlockItem,
    VariantContentItem,
    VariantContentSnapshot,
)

VARIANT_PRINT_BLOCK_TASK = 'task'
VARIANT_PRINT_BLOCK_BLANK_CELLS = 'blank_cells'
VARIANT_PRINT_BLOCK_PAGE_BREAK = 'page_break'
VARIANT_PRINT_BLOCK_THEORY = 'theory'
VARIANT_PRINT_BLOCK_TEXT = 'text'

VARIANT_PRINT_BLOCK_TYPES = frozenset(
    (
        VARIANT_PRINT_BLOCK_TASK,
        VARIANT_PRINT_BLOCK_BLANK_CELLS,
        VARIANT_PRINT_BLOCK_PAGE_BREAK,
        VARIANT_PRINT_BLOCK_THEORY,
        VARIANT_PRINT_BLOCK_TEXT,
    )
)

@dataclass(frozen=True)
class VariantPrintOverrides:
    """Temporary visibility overrides for one variant render."""

    hidden_content_types: Tuple[str, ...] = field(default_factory=tuple)
    hide_blank_cells: bool = False

    def __post_init__(self):
        hidden_content_types = _tuple_option(self.hidden_content_types)
        unsupported_types = (
            set(hidden_content_types) - VARIANT_STATIC_CONTENT_TYPES
        )
        if unsupported_types:
            unsupported = ', '.join(sorted(unsupported_types))
            raise ValueError(
                f'Unsupported hidden content types: {unsupported}',
            )
        object.__setattr__(
            self,
            'hidden_content_types',
            hidden_content_types,
        )

    def blank_cells_options(self, item: VariantContentItem) -> Mapping[str, Any]:
        if self.hide_blank_cells:
            return {}
        if not item.blank_cells_after:
            return {}
        return {'rows': item.blank_cells_rows}

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
    overrides: VariantPrintOverrides | None = None,
) -> VariantPrintPlan:
    overrides = overrides or VariantPrintOverrides()
    ordered_block_groups = []
    for row in content_snapshot.items:
        task_blocks = [_task_print_block(row)]
        blank_cells_options = overrides.blank_cells_options(row)
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
        if row.page_break_after:
            task_blocks.append(
                VariantPrintBlock(
                    block_type=VARIANT_PRINT_BLOCK_PAGE_BREAK,
                    variant_task_id=row.variant_task_id,
                    task_id=row.task_id,
                    source_selection_id=row.source_selection_id,
                    order=row.order,
                    content_order=_task_content_order(row),
                    content_role=row.bank_role,
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
        if not overrides.includes_content_block(block):
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


def _task_print_block(row: VariantContentItem) -> VariantPrintBlock:
    return VariantPrintBlock(
        block_type=VARIANT_PRINT_BLOCK_TASK,
        variant_task_id=row.variant_task_id,
        task_id=row.task_id,
        source_selection_id=row.source_selection_id,
        order=row.order,
        content_order=_task_content_order(row),
        content_role=row.bank_role,
        source_render_mode=row.render_mode,
        render_mode=row.render_mode,
        options={
            'bank_role': row.bank_role,
            'render_mode': row.render_mode,
            'is_assessable': row.is_assessable,
            'max_points': row.max_points,
        },
    )


def build_variant_print_overrides_from_options(
    options,
) -> VariantPrintOverrides:
    options = dict(options or {})
    return VariantPrintOverrides(
        hidden_content_types=_tuple_option(
            options.get('hidden_content_types'),
        ),
        hide_blank_cells=bool(options.get('hide_blank_cells', False)),
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
