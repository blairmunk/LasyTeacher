"""Command data for creating and updating work specifications."""

from dataclasses import dataclass, field

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
    TASK_RENDER_MODE_TASK_ONLY,
)
from core_logic.value_objects.work_assessment import (
    WORK_ASSESSMENT_MODE_VARIANT,
    validate_work_assessment_mode,
)


@dataclass(frozen=True)
class CreateWorkParams:
    name: str
    work_type: str = 'remedial'
    duration: int = 45
    max_score: int = 0
    variant_counter: int = 0
    work_id: str = ''
    assessment_mode: str = WORK_ASSESSMENT_MODE_VARIANT

    def __post_init__(self):
        validate_work_assessment_mode(self.assessment_mode)


@dataclass(frozen=True)
class WorkTaskSelectionParams:
    analog_group_id: str
    order: int
    count: int
    weight: int
    bank_role_filter: str = TASK_BANK_ROLE_ANY
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_cells_rows: int = DEFAULT_BLANK_CELLS_ROWS


@dataclass(frozen=True)
class WorkContentBlockParams:
    content_type: str
    order: int
    title: str = ''
    body: str = ''
    topic_ids: tuple[str, ...] = field(default_factory=tuple)
    include_subtopics: bool = False

    def __post_init__(self):
        object.__setattr__(self, 'topic_ids', tuple(self.topic_ids))


@dataclass(frozen=True)
class CreateWorkWithSpecificationParams:
    work: CreateWorkParams
    specs: tuple[WorkTaskSelectionParams, ...]
    content_blocks: tuple[WorkContentBlockParams, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'specs', tuple(self.specs))
        object.__setattr__(self, 'content_blocks', tuple(self.content_blocks))


@dataclass(frozen=True)
class WorkUpdateContext:
    work_id: str
    assessment_mode: str
    has_variants: bool = False
    has_events: bool = False

    @property
    def assessment_mode_locked(self) -> bool:
        return self.has_variants or self.has_events
