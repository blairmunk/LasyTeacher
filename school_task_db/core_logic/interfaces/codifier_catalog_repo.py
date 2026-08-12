"""Read port for the codifier catalog."""

from abc import ABC, abstractmethod
from typing import Any


class ICodifierCatalogRepository(ABC):
    @abstractmethod
    def get_list_codifiers(self) -> Any:
        """Return codifiers for the codifier list page."""
