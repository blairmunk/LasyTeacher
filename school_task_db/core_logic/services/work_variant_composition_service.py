"""Build immutable variant creation plans from a work specification."""

from dataclasses import dataclass, field
import random
from typing import Any, Callable, Mapping, Tuple

from core_logic.services.work_score_allocation_service import (
    WorkScoreAllocationService,
    WorkScoreSpecRow,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_CONTROL,
    TASK_RENDER_MODE_TASK_ONLY,
)


@dataclass(frozen=True)
class AvailableVariantTask:
    task_id: str
    bank_role: str = TASK_BANK_ROLE_CONTROL


@dataclass(frozen=True)
class WorkVariantSpecRow:
    spec_row_id: str
    count: int
    weight: int
    content_order: int = 0
    available_tasks: Tuple[AvailableVariantTask, ...] = field(
        default_factory=tuple,
    )
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_cells_rows: int = DEFAULT_BLANK_CELLS_ROWS

    def __post_init__(self):
        object.__setattr__(self, 'available_tasks', tuple(self.available_tasks))


@dataclass(frozen=True)
class WorkVariantCompositionInput:
    work_name: str
    duration: int
    max_score: int
    effective_max_score: int
    variant_counter: int
    spec_rows: Tuple[WorkVariantSpecRow, ...] = field(default_factory=tuple)
    content_blocks: Tuple["WorkVariantContentBlock", ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'spec_rows', tuple(self.spec_rows))
        object.__setattr__(
            self,
            'content_blocks',
            tuple(self.content_blocks),
        )


@dataclass(frozen=True)
class WorkVariantContentBlock:
    source_content_id: str
    content_type: str
    order: int
    title: str = ''
    content: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, 'content', dict(self.content))


@dataclass(frozen=True)
class VariantTaskCreationPlan:
    task_id: str
    source_selection_id: str
    content_order: int
    order: int
    max_points: int
    weight: int
    bank_role: str
    render_mode: str
    is_assessable: bool
    blank_cells_after: bool
    blank_cells_rows: int


@dataclass(frozen=True)
class VariantCreationPlan:
    number: int
    work_name_snapshot: str
    max_score_snapshot: int
    duration_snapshot: int
    tasks: Tuple[VariantTaskCreationPlan, ...] = field(default_factory=tuple)
    content_blocks: Tuple["VariantContentBlockCreationPlan", ...] = field(
        default_factory=tuple,
    )


@dataclass(frozen=True)
class VariantContentBlockCreationPlan:
    source_content_id: str
    content_type: str
    order: int
    title: str = ''
    content: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, 'content', dict(self.content))


@dataclass(frozen=True)
class WorkVariantCompositionPlan:
    variants: Tuple[VariantCreationPlan, ...]
    next_variant_counter: int


class WorkVariantCompositionService:
    def __init__(
        self,
        task_selector: Callable | None = None,
        score_allocation_service=None,
    ):
        self.task_selector = task_selector or random.sample
        self.score_allocation_service = (
            score_allocation_service or WorkScoreAllocationService()
        )

    def compose(
        self,
        composition_input: WorkVariantCompositionInput,
        count: int,
    ) -> WorkVariantCompositionPlan:
        if count < 1:
            raise ValueError('count must be positive')

        score_allocations = self.score_allocation_service.allocate(
            max_score=composition_input.max_score,
            spec_rows=(
                WorkScoreSpecRow(
                    spec_row_id=row.spec_row_id,
                    count=row.count,
                    weight=row.weight,
                    is_assessable=row.is_assessable,
                )
                for row in composition_input.spec_rows
            ),
        )
        variants = tuple(
            self._compose_variant(
                composition_input,
                number=composition_input.variant_counter + offset,
                score_allocations=score_allocations,
            )
            for offset in range(1, count + 1)
        )
        return WorkVariantCompositionPlan(
            variants=variants,
            next_variant_counter=composition_input.variant_counter + count,
        )

    def _compose_variant(
        self,
        composition_input,
        number,
        score_allocations,
    ):
        tasks = []
        score_index = 0
        task_order = 1
        for row in composition_input.spec_rows:
            selected_tasks = self._select_tasks(row)
            for task in selected_tasks:
                max_points = (
                    score_allocations[score_index].points
                    if score_index < len(score_allocations)
                    else 0
                )
                tasks.append(
                    VariantTaskCreationPlan(
                        task_id=task.task_id,
                        source_selection_id=row.spec_row_id,
                        content_order=row.content_order,
                        order=task_order,
                        max_points=max_points,
                        weight=row.weight,
                        bank_role=task.bank_role,
                        render_mode=row.render_mode,
                        is_assessable=row.is_assessable,
                        blank_cells_after=row.blank_cells_after,
                        blank_cells_rows=row.blank_cells_rows,
                    )
                )
                task_order += 1
                score_index += 1

        return VariantCreationPlan(
            number=number,
            work_name_snapshot=composition_input.work_name,
            max_score_snapshot=composition_input.effective_max_score,
            duration_snapshot=composition_input.duration,
            tasks=tuple(tasks),
            content_blocks=tuple(
                VariantContentBlockCreationPlan(
                    source_content_id=block.source_content_id,
                    content_type=block.content_type,
                    order=block.order,
                    title=block.title,
                    content=block.content,
                )
                for block in composition_input.content_blocks
            ),
        )

    def _select_tasks(self, row):
        if len(row.available_tasks) < row.count:
            return row.available_tasks
        return tuple(self.task_selector(row.available_tasks, row.count))
