"""Codifier repository interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from core_logic.entities.codifier import (
    CodifierContentEntry,
    CodifierDetailSpec,
    CodifierRequirement,
)


class ICodifierRepository(ABC):
    @abstractmethod
    def get_list_codifiers(self) -> Any:
        """Return codifiers for the codifier list page."""

    @abstractmethod
    def get_codifier(self, codifier_id: str) -> Optional[CodifierDetailSpec]:
        """Return one codifier detail read model by id or None."""

    @abstractmethod
    def get_content_tree(self, codifier_id: str) -> List[CodifierContentEntry]:
        """Return root content entry read models for one codifier."""

    @abstractmethod
    def get_requirements(self, codifier_id: str) -> List[CodifierRequirement]:
        """Return requirement read models for one codifier."""

    @abstractmethod
    def get_coverage(self, codifier_id: str) -> dict:
        """Return content coverage for one codifier."""
