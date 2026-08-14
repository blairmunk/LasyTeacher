"""Immutable read models used to build work documents."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_SPACE_AREA_CM2,
    TASK_BANK_ROLE_CONTROL,
    TASK_RENDER_MODE_TASK_ONLY,
)


@dataclass(frozen=True)
class WorkDocumentScoreSpecRow:
    pk: str
    count: int
    weight: int
    is_assessable: bool = True


@dataclass(frozen=True)
class WorkDocumentTaskSource:
    pk: str
    task_id: str
    task_snapshot: Mapping[str, Any]
    order: int
    max_points: int
    source_selection_id: str = ''
    content_order: int = 0
    bank_role: str = TASK_BANK_ROLE_CONTROL
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_space_area_cm2: int = DEFAULT_BLANK_SPACE_AREA_CM2
    page_break_after: bool = False

    def __post_init__(self):
        object.__setattr__(self, 'task_snapshot', dict(self.task_snapshot))


@dataclass(frozen=True)
class WorkDocumentContentBlockSource:
    pk: str
    source_content_id: str
    content_type: str
    order: int
    title: str = ''
    content: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, 'content', dict(self.content))


@dataclass(frozen=True)
class WorkDocumentVariantSource:
    pk: str
    number: int
    max_score_snapshot: int
    duration_snapshot: int
    tasks: Tuple[WorkDocumentTaskSource, ...] = field(default_factory=tuple)
    content_blocks: Tuple[WorkDocumentContentBlockSource, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'tasks', tuple(self.tasks))
        object.__setattr__(self, 'content_blocks', tuple(self.content_blocks))


@dataclass(frozen=True)
class WorkDocumentSource:
    pk: str
    name: str
    work_type: str
    duration: int
    max_score: int
    score_spec_rows: Tuple[WorkDocumentScoreSpecRow, ...] = field(
        default_factory=tuple,
    )
    variants: Tuple[WorkDocumentVariantSource, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'score_spec_rows', tuple(self.score_spec_rows))
        object.__setattr__(self, 'variants', tuple(self.variants))
