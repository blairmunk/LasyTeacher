"""Command repository port for variant detach and deletion workflows."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.work import VariantDeletionOutcome


class IVariantLifecycleCommandRepository(ABC):
    @abstractmethod
    def detach_variant_from_work(self, variant_id: str) -> str:
        """Detach a variant and return its short identifier."""

    @abstractmethod
    def delete_variant_if_unreferenced(
        self,
        variant_id: str,
    ) -> VariantDeletionOutcome:
        """Atomically delete an unreferenced variant and return the outcome."""

    @abstractmethod
    def bulk_delete_work_variants(
        self,
        work_id: str,
        variant_ids: List[str],
    ) -> int:
        """Delete selected variants belonging to a work."""
