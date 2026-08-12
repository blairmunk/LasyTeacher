"""Read port for codifier structure and coverage."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.codifier import (
    CodifierContentEntry,
    CodifierDetailSpec,
    CodifierRequirement,
)


class ICodifierDetailRepository(ABC):
    @abstractmethod
    def get_codifier(self, codifier_id: str) -> Optional[CodifierDetailSpec]:
        """Return one codifier detail read model by id or None."""

    @abstractmethod
    def get_content_tree(self, codifier_id: str) -> List[CodifierContentEntry]:
        """Return root content entries for one codifier."""

    @abstractmethod
    def get_requirements(self, codifier_id: str) -> List[CodifierRequirement]:
        """Return requirement read models for one codifier."""

    @abstractmethod
    def get_coverage(self, codifier_id: str) -> dict:
        """Return content coverage for one codifier."""
