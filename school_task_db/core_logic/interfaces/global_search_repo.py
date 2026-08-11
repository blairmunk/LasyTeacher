"""Read port for global application search."""

from abc import ABC, abstractmethod
from typing import Dict, List


class IGlobalSearchRepository(ABC):
    @abstractmethod
    def search_by_uuid(self, query: str) -> Dict[str, object]:
        """Return global search results by UUID fragment."""

    @abstractmethod
    def search_by_text(self, words: List[str]) -> Dict[str, object]:
        """Return global search results by text words."""
