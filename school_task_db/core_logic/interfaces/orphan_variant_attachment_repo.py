"""Repository port for attaching orphan variants to a new work."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.orphan_variant_commands import (
    CreatedWorkFromOrphanVariantsRef,
    CreateWorkFromOrphanVariantsParams,
)
from core_logic.entities.work import OrphanVariantRef


class IOrphanVariantAttachmentRepository(ABC):
    @abstractmethod
    def get_orphan_variant_refs(
        self,
        variant_ids: List[str],
    ) -> List[OrphanVariantRef]:
        """Return selected orphan variant refs ordered for attaching."""

    @abstractmethod
    def create_work_from_orphan_variants(
        self,
        params: CreateWorkFromOrphanVariantsParams,
    ) -> Optional[CreatedWorkFromOrphanVariantsRef]:
        """Create a work and attach all selected orphan variants atomically."""
