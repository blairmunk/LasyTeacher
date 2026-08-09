"""Task source repository interface."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.task import (
    SourceCreateParams,
    SourceCreateResult,
    SourceListItem,
)


class ISourceRepository(ABC):
    @abstractmethod
    def get_source_list_sources(self) -> List[SourceListItem]:
        """Return task sources with aggregate usage counts."""

    @abstractmethod
    def create_source(self, params: SourceCreateParams) -> SourceCreateResult:
        """Create a task source and return its read model."""
