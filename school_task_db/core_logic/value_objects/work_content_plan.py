"""Pedagogical content plan for a work."""

from dataclasses import dataclass, field
from typing import Tuple, Union

from core_logic.value_objects.work_specification import (
    WorkTaskSelectionSpec,
)

WORK_CONTENT_TASK_SELECTION = 'task_selection'
WORK_CONTENT_THEORY = 'theory'
WORK_CONTENT_TEXT = 'text'
WORK_CONTENT_ORIGINAL_MISTAKES = 'original_mistakes'
WORK_CONTENT_TRAINING_TASKS = 'training_tasks'

@dataclass(frozen=True)
class WorkTaskSelectionBlock:
    selection: WorkTaskSelectionSpec
    title: str = ''
    content_type: str = field(
        default=WORK_CONTENT_TASK_SELECTION,
        init=False,
    )

    @property
    def order(self) -> int:
        return self.selection.order


@dataclass(frozen=True)
class WorkTheoryBlock:
    order: int
    title: str = ''
    topic_ids: Tuple[str, ...] = field(default_factory=tuple)
    include_subtopics: bool = False
    content_type: str = field(default=WORK_CONTENT_THEORY, init=False)

    def __post_init__(self):
        object.__setattr__(self, 'topic_ids', tuple(self.topic_ids))


@dataclass(frozen=True)
class WorkTextBlock:
    order: int
    body: str
    title: str = ''
    content_type: str = field(default=WORK_CONTENT_TEXT, init=False)


@dataclass(frozen=True)
class WorkOriginalMistakesBlock:
    order: int
    title: str = ''
    content_type: str = field(
        default=WORK_CONTENT_ORIGINAL_MISTAKES,
        init=False,
    )


@dataclass(frozen=True)
class WorkTrainingTasksBlock:
    order: int
    title: str = ''
    content_type: str = field(
        default=WORK_CONTENT_TRAINING_TASKS,
        init=False,
    )


WORK_CONTENT_BLOCK_TYPES = (
    WorkTaskSelectionBlock,
    WorkTheoryBlock,
    WorkTextBlock,
    WorkOriginalMistakesBlock,
    WorkTrainingTasksBlock,
)

WorkContentBlock = Union[
    WorkTaskSelectionBlock,
    WorkTheoryBlock,
    WorkTextBlock,
    WorkOriginalMistakesBlock,
    WorkTrainingTasksBlock,
]


@dataclass(frozen=True)
class WorkContentPlan:
    blocks: Tuple[WorkContentBlock, ...] = field(default_factory=tuple)

    def __post_init__(self):
        blocks = tuple(self.blocks)
        for block in blocks:
            if not isinstance(block, WORK_CONTENT_BLOCK_TYPES):
                raise ValueError(
                    f'Unsupported work content block: {type(block).__name__}',
                )
        object.__setattr__(
            self,
            'blocks',
            tuple(sorted(blocks, key=lambda block: block.order)),
        )

    @property
    def task_selection_blocks(self) -> Tuple[WorkTaskSelectionBlock, ...]:
        return tuple(
            block
            for block in self.blocks
            if isinstance(block, WorkTaskSelectionBlock)
        )

    @property
    def task_selections(self) -> Tuple[WorkTaskSelectionSpec, ...]:
        return tuple(
            block.selection
            for block in self.task_selection_blocks
        )


def build_work_content_plan(
    task_rows=(),
    content_rows=(),
) -> WorkContentPlan:
    return WorkContentPlan(
        blocks=(
            tuple(
                WorkTaskSelectionBlock(
                    title=row.analog_group.name,
                    selection=WorkTaskSelectionSpec(
                        analog_group_id=str(row.analog_group.pk),
                        count=row.count,
                        order=row.order,
                        bank_role_filter=row.bank_role_filter,
                        render_mode=row.render_mode,
                        is_assessable=row.is_assessable,
                        blank_cells_after=row.blank_cells_after,
                        blank_cells_rows=row.blank_cells_rows,
                        weight=row.weight,
                    ),
                )
                for row in task_rows
            )
            + tuple(
                _persistent_content_block(row)
                for row in content_rows
            )
        ),
    )


def build_work_content_plan_from_task_rows(rows) -> WorkContentPlan:
    return build_work_content_plan(task_rows=rows)


def _persistent_content_block(row) -> WorkContentBlock:
    if row.content_type == WORK_CONTENT_THEORY:
        return WorkTheoryBlock(
            order=row.order,
            title=row.title,
            topic_ids=tuple(row.topic_ids),
            include_subtopics=row.include_subtopics,
        )
    if row.content_type == WORK_CONTENT_TEXT:
        return WorkTextBlock(
            order=row.order,
            title=row.title,
            body=row.body,
        )
    raise ValueError(
        f'Unsupported persistent work content: {row.content_type}',
    )
