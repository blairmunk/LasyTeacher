"""Read port for the codifier catalog."""

from abc import ABC, abstractmethod
from typing import Sequence

from core_logic.entities.codifier import CodifierListItem


class ICodifierCatalogRepository(ABC):
    @abstractmethod
    def get_list_codifiers(self) -> Sequence[CodifierListItem]:
        """Return codifiers for the codifier list page."""
