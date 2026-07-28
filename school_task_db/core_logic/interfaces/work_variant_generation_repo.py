"""Repository interface for generating variants from work specifications."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.work import (
    VariantGenerationGroup,
    VariantGenerationWork,
)
from core_logic.entities.work_variant_composition import (
    WorkVariantCompositionInput,
    WorkVariantCompositionPlan,
    WorkVariantCompositionSaveResult,
)
from core_logic.entities.work_spec_sync import (
    WorkSpecSyncItem,
    WorkSpecSyncSaveResult,
    WorkSpecSyncSource,
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
    def get_variant_composition_input(
        self,
        work_id: str,
    ) -> Optional[WorkVariantCompositionInput]:
        """Return an immutable source snapshot for variant composition."""

    @abstractmethod
    def save_variant_composition_plan(
        self,
        work_id: str,
        expected_variant_counter: int,
        plan: WorkVariantCompositionPlan,
    ) -> WorkVariantCompositionSaveResult:
        """Persist a plan if the work counter still matches the source."""

    @abstractmethod
    def get_work_spec_sync_source(
        self,
        work_id: str,
    ) -> Optional[WorkSpecSyncSource]:
        """Return variant group snapshots used to restore a specification."""

    @abstractmethod
    def save_work_spec_sync_plan(
        self,
        work_id: str,
        expected_variant_counter: int,
        plan: tuple[WorkSpecSyncItem, ...],
    ) -> WorkSpecSyncSaveResult:
        """Persist a sync plan if its variant source is still current."""
