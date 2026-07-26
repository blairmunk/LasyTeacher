"""Repository port for orphan variant workflows."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from core_logic.entities.work import OrphanVariantListItem, OrphanVariantRef


@dataclass(frozen=True)
class CreateWorkFromOrphanVariantsParams:
    name: str
    work_type: str
    max_score: int
    variant_ids: List[str]


@dataclass(frozen=True)
class CreatedWorkFromOrphanVariantsRef:
    work_id: str
    variant_count: int


class IOrphanVariantRepository(ABC):
    @abstractmethod
    def get_orphan_variants(self) -> List[OrphanVariantListItem]:
        """Return orphan variants for the orphan list page."""

    @abstractmethod
    def count_orphan_variants(self) -> int:
        """Return orphan variant count."""

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
