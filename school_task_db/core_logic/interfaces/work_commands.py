"""Command data transferred to work repository ports."""

from dataclasses import dataclass, field
from typing import List, Optional

from core_logic.entities.work_variant_composition import VariantCreationPlan
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
class CreateVariantParams:
    work_id: Optional[str]
    student_id: str
    plan: VariantCreationPlan
    source_work_id: Optional[str] = None
    source_participation_id: Optional[str] = None
    source_attempt_snapshot_id: Optional[str] = None
    variant_type: str = 'remedial'


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
    topic_ids: List[str] = field(default_factory=list)
    include_subtopics: bool = False


@dataclass(frozen=True)
class CreateWorkWithSpecificationParams:
    work: CreateWorkParams
    specs: List[WorkTaskSelectionParams]
    content_blocks: List[WorkContentBlockParams] = field(
        default_factory=list,
    )


@dataclass(frozen=True)
class WorkUpdateContext:
    work_id: str
    assessment_mode: str
    has_variants: bool = False
    has_events: bool = False

    @property
    def assessment_mode_locked(self) -> bool:
        return self.has_variants or self.has_events


@dataclass(frozen=True)
class NewWorkVariantParams:
    student_id: str
    plan: VariantCreationPlan
    source_work_id: Optional[str] = None
    source_participation_id: Optional[str] = None
    source_attempt_snapshot_id: Optional[str] = None
    variant_type: str = 'remedial'


@dataclass(frozen=True)
class CreateWorkWithVariantsParams:
    work: CreateWorkParams
    variants: List[NewWorkVariantParams]


@dataclass(frozen=True)
class CreatedWorkWithVariantsRef:
    work_id: str
    variant_ids: List[str]


@dataclass(frozen=True)
class CreateWorkWithVariantFromTasksParams:
    name: str
    work_type: str
    task_ids: List[str]


@dataclass(frozen=True)
class CreatedWorkVariantRef:
    work_id: str
    variant_id: str
    tasks_count: int
