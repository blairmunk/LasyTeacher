"""Read port for merged subject reference catalogs."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.task import ReferenceElementOption


class ITaskReferenceCatalogRepository(ABC):
    @abstractmethod
    def get_reference_element_options(
        self,
        subject: str,
        category: str,
    ) -> List[ReferenceElementOption]:
        """Return merged active reference options."""
