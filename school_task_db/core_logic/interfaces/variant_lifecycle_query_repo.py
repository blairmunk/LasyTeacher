"""Read-only repository port for variant lifecycle decisions."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.work import VariantDeleteInfo


class IVariantLifecycleQueryRepository(ABC):
    @abstractmethod
    def get_variant_delete_info(
        self,
        variant_id: str,
    ) -> Optional[VariantDeleteInfo]:
        """Return information required to decide how a variant can be removed."""

    @abstractmethod
    def count_work_variants(self, work_id: str) -> int:
        """Return the number of variants still attached to a work."""
