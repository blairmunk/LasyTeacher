"""Repository interface for saving work specifications."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.work_specification_commands import (
    CreateWorkWithSpecificationParams,
    WorkUpdateContext,
)


class IWorkSpecificationRepository(ABC):
    @abstractmethod
    def get_work_update_context(
        self,
        work_id: str,
    ) -> Optional[WorkUpdateContext]:
        """Return facts needed to validate a work update."""

    @abstractmethod
    def update_work_with_specification(
        self,
        params: CreateWorkWithSpecificationParams,
    ) -> bool:
        """Atomically update a work and its complete content plan."""

    @abstractmethod
    def create_work_with_specification(
        self,
        params: CreateWorkWithSpecificationParams,
    ) -> str:
        """Create a work and its specification atomically."""
