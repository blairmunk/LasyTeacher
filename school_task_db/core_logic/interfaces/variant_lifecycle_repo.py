"""Repository port for variant detach and deletion workflows."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.work import VariantDeleteInfo


class IVariantLifecycleRepository(ABC):
    @abstractmethod
    def get_variant_delete_info(
        self,
        variant_id: str,
    ) -> Optional[VariantDeleteInfo]:
        """Return information required to decide how a variant can be removed."""

    @abstractmethod
    def detach_variant_from_work(self, variant_id: str) -> str:
        """Detach a variant and return its short identifier."""

    @abstractmethod
    def delete_variant(self, variant_id: str) -> str:
        """Delete a variant and return its previous work ID, if any."""

    @abstractmethod
    def bulk_delete_work_variants(
        self,
        work_id: str,
        variant_ids: List[str],
    ) -> int:
        """Delete selected variants belonging to a work."""

    @abstractmethod
    def count_work_variants(self, work_id: str) -> int:
        """Return the number of variants still attached to a work."""
