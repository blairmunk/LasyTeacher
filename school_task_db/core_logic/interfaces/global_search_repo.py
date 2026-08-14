"""Read port for global application search."""

from abc import ABC, abstractmethod
from typing import Sequence

from core_logic.entities.core import GlobalSearchResults


class IGlobalSearchRepository(ABC):
    @abstractmethod
    def search_by_uuid(self, query: str) -> GlobalSearchResults:
        """Return results whose own UUID ends with the fragment."""

    @abstractmethod
    def search_by_text(self, words: Sequence[str]) -> GlobalSearchResults:
        """Return global search results by text words."""
