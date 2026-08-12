"""Command repository port for task sources."""

from abc import ABC, abstractmethod

from core_logic.entities.task import SourceCreateParams, SourceCreateResult


class ISourceCommandRepository(ABC):
    @abstractmethod
    def create_source(self, params: SourceCreateParams) -> SourceCreateResult:
        """Create a task source and return its read model."""
