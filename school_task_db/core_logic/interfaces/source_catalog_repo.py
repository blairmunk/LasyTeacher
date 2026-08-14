"""Read-only repository port for the task source catalog."""

from abc import ABC, abstractmethod
from core_logic.entities.task import SourceListItem


class ISourceCatalogRepository(ABC):
    @abstractmethod
    def get_source_list_sources(self) -> tuple[SourceListItem, ...]:
        """Return task sources with aggregate usage counts."""
