"""Work repository interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Set
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
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
class CreateVariantParams:
    work_id: Optional[str]
    number: int
    student_id: str
    task_ids: List[str]
    work_name_snapshot: str
    max_score_snapshot: int
    source_work_id: Optional[str] = None
    variant_type: str = 'remedial'


@dataclass(frozen=True)
class WorkSpecificationRowParams:
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
class CreateWorkWithSpecificationParams:
    work: CreateWorkParams
    specs: List[WorkSpecificationRowParams]


@dataclass(frozen=True)
class NewWorkVariantParams:
    number: int
    student_id: str
    task_ids: List[str]
    max_score_snapshot: int
    source_work_id: Optional[str] = None
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
    def get_variant_task_ids(self, work_id: str) -> Set[str]:
        """Return task IDs used in all variants of a work."""

    @abstractmethod
    def get_student_variant_task_ids(
        self,
        work_id: str,
        student_id: str,
        event_id: str,
    ) -> Set[str]:
        """Return task IDs from a concrete student's variant for an event."""

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
        specs: List[WorkSpecificationRowParams],
    ) -> bool:
        """Replace a work specification and return whether the work was found."""

    @abstractmethod
    def create_variant_with_tasks(self, params: CreateVariantParams) -> str:
        """Create a variant with VariantTask rows and return the variant ID."""

    @abstractmethod
    def create_work_with_variant_from_tasks(
        self,
        params: CreateWorkWithVariantFromTasksParams,
    ) -> CreatedWorkVariantRef:
        """Create a work and its first variant from selected tasks."""
