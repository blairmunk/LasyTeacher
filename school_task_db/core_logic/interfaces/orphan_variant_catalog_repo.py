"""Read-only repository port for the orphan variant catalog."""

from abc import ABC, abstractmethod

from core_logic.entities.work import OrphanVariantListItem


class IOrphanVariantCatalogRepository(ABC):
    @abstractmethod
    def get_orphan_variants(self) -> tuple[OrphanVariantListItem, ...]:
        """Return orphan variants for the orphan list page."""

    @abstractmethod
    def count_orphan_variants(self) -> int:
        """Return orphan variant count."""
