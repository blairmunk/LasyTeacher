"""Read port for the work variant generation form."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.work import (
    VariantGenerationGroupSource,
    VariantGenerationWork,
)


class IVariantGenerationFormRepository(ABC):
    @abstractmethod
    def get_work_generation_target(
        self,
        work_id: str,
    ) -> Optional[VariantGenerationWork]:
        """Return the work facts required by the generation form."""

    @abstractmethod
    def get_variant_generation_group_sources(
        self,
        work_id: str,
    ) -> tuple[VariantGenerationGroupSource, ...]:
        """Return unfiltered specification facts for the form."""
