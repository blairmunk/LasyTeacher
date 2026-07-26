"""Repository interface for work-backed document rendering."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.work import RemedialSheetData


class IWorkDocumentRepository(ABC):
    @abstractmethod
    def get_work_name(self, work_id: str) -> Optional[str]:
        """Return a work name, or None when the work does not exist."""

    @abstractmethod
    def get_work_variant_ids(self, work_id: str) -> List[str]:
        """Return ordered variant IDs for rendering a work document."""

    @abstractmethod
    def get_work_remedial_variant_ids(self, work_id: str) -> List[str]:
        """Return ordered remedial variant IDs for batch rendering."""

    @abstractmethod
    def get_variant_type(self, variant_id: str) -> Optional[str]:
        """Return variant type, or None when the variant does not exist."""

    @abstractmethod
    def get_remedial_sheet_data(self, variant_id: str) -> RemedialSheetData:
        """Return source data for rendering one remedial sheet."""
