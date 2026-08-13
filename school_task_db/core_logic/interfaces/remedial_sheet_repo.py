"""Repository interface for remedial sheet document sources."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.work import RemedialSheetSource


class IRemedialSheetRepository(ABC):
    @abstractmethod
    def get_work_personal_remedial_variant_ids(
        self,
        work_id: str,
    ) -> tuple[str, ...]:
        """Return ordered personalized remedial variant IDs."""

    @abstractmethod
    def get_variant_type(self, variant_id: str) -> Optional[str]:
        """Return variant type, or None when the variant does not exist."""

    @abstractmethod
    def get_remedial_sheet_source(
        self,
        variant_id: str,
    ) -> Optional[RemedialSheetSource]:
        """Return normalized remedial facts, if the variant exists."""
