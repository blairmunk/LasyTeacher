"""Work repository interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_CONTROL,
    TASK_RENDER_MODE_TASK_ONLY,
)


@dataclass(frozen=True)
class CreateWorkParams:
    name: str
    work_type: str = 'remedial'
    duration: int = 45
    max_score: int = 0
    variant_counter: int = 0
    work_id: str = ''


@dataclass(frozen=True)
class VariantTaskSnapshotParams:
    task_id: str
    order: int
    max_points: int
    source_selection_id: str = ''
    content_order: int = 0
    bank_role: str = TASK_BANK_ROLE_CONTROL
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_cells_rows: int = DEFAULT_BLANK_CELLS_ROWS


@dataclass(frozen=True)
class CreateVariantParams:
    work_id: Optional[str]
    number: int
    student_id: str
    task_snapshots: List[VariantTaskSnapshotParams]
    work_name_snapshot: str
    max_score_snapshot: int
    source_work_id: Optional[str] = None
    source_participation_id: Optional[str] = None
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
class NewWorkVariantParams:
    number: int
    student_id: str
    task_snapshots: List[VariantTaskSnapshotParams]
    max_score_snapshot: int
    source_work_id: Optional[str] = None
    source_participation_id: Optional[str] = None
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


class IWorkRepository(ABC):
    @abstractmethod
    def create_work(self, params: CreateWorkParams) -> str:
        """Create a work and return its ID."""

    @abstractmethod
    def update_work(self, params: CreateWorkParams) -> bool:
        """Update a work and return whether it was found."""

    @abstractmethod
    def create_work_with_specification(
        self,
        params: CreateWorkWithSpecificationParams,
    ) -> str:
        """Create a work and its specification atomically."""

    @abstractmethod
    def create_work_with_variants(
        self,
        params: CreateWorkWithVariantsParams,
    ) -> CreatedWorkWithVariantsRef:
        """Create a work and all supplied variants atomically."""

    @abstractmethod
    def replace_work_analog_groups(
        self,
        work_id: str,
        specs: List[WorkTaskSelectionParams],
    ) -> bool:
        """Replace a work specification and return whether the work was found."""

    @abstractmethod
    def replace_work_content_plan(
        self,
        work_id: str,
        specs: List[WorkTaskSelectionParams],
        content_blocks: List[WorkContentBlockParams],
    ) -> bool:
        """Replace all persistent work content atomically."""

    @abstractmethod
    def create_variant_with_tasks(self, params: CreateVariantParams) -> str:
        """Create a variant with VariantTask rows and return the variant ID."""

    @abstractmethod
    def create_work_with_variant_from_tasks(
        self,
        params: CreateWorkWithVariantFromTasksParams,
    ) -> CreatedWorkVariantRef:
        """Create a work and its first variant from selected tasks."""
