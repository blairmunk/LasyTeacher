"""Repository interface for generating variants from work specifications."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.work import (
    VariantGenerationGroup,
    VariantGenerationWork,
)


class IWorkVariantGenerationRepository(ABC):
    @abstractmethod
    def get_work_generation_target(
        self,
        work_id: str,
    ) -> Optional[VariantGenerationWork]:
        """Return a work read model for the variant generation form."""

    @abstractmethod
    def get_variant_generation_groups(
        self,
        work_id: str,
    ) -> List[VariantGenerationGroup]:
        """Return work specification rows for the generation form."""

    @abstractmethod
    def compose_variants(self, work_id: str, count: int) -> Optional[int]:
        """Compose variants atomically, or return None when work is missing."""

    @abstractmethod
    def sync_analog_groups_from_variants(
        self,
        work_id: str,
    ) -> Optional[int]:
        """Sync specification atomically, or return None when work is missing."""
