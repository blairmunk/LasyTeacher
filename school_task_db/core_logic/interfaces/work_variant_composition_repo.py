"""Persistence port for composing variants from a work specification."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.work_variant_composition import (
    WorkVariantCompositionPlan,
    WorkVariantCompositionSaveResult,
    WorkVariantCompositionSource,
)


class IWorkVariantCompositionRepository(ABC):
    @abstractmethod
    def get_variant_composition_source(
        self,
        work_id: str,
    ) -> Optional[WorkVariantCompositionSource]:
        """Return immutable facts used to compose work variants."""

    @abstractmethod
    def save_variant_composition_plan(
        self,
        work_id: str,
        expected_variant_counter: int,
        plan: WorkVariantCompositionPlan,
    ) -> WorkVariantCompositionSaveResult:
        """Persist a plan if the work counter still matches its source."""
