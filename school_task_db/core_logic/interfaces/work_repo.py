"""Work repository interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Set


@dataclass(frozen=True)
class CreateWorkParams:
    name: str
    work_type: str = 'remedial'
    max_score: int = 0
    variant_counter: int = 0


@dataclass(frozen=True)
class CreateVariantParams:
    work_id: str
    number: int
    student_id: str
    task_ids: List[str]
    work_name_snapshot: str
    max_score_snapshot: int
    source_work_id: Optional[str] = None
    variant_type: str = 'remedial'


class IWorkRepository(ABC):
    @abstractmethod
    def get_detail_variants(self, work_id: str) -> Any:
        """Return variants for the work detail page."""

    @abstractmethod
    def get_detail_analog_groups(self, work_id: str) -> List[Any]:
        """Return analog groups for the work detail page."""

    @abstractmethod
    def get_spec_preview(self, work_id: str) -> List[Any]:
        """Return points specification preview for the work detail page."""

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
    def create_variant_with_tasks(self, params: CreateVariantParams) -> str:
        """Create a variant with VariantTask rows and return the variant ID."""
