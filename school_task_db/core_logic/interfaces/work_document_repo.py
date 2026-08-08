"""Repository interface for work-backed document rendering."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.work import RemedialSheetSource, WorkDocumentRef
from core_logic.entities.work_document import WorkDocumentSource


class IWorkDocumentRepository(ABC):
    @abstractmethod
    def get_work_document_source(
        self,
        work_id: str,
    ) -> Optional[WorkDocumentSource]:
        """Return the complete immutable source needed by document builders."""

    @abstractmethod
    def get_work_document_ref(
        self,
        work_id: str,
    ) -> Optional[WorkDocumentRef]:
        """Return document-facing work data, or None when it is missing."""

    @abstractmethod
    def get_work_variant_ids(self, work_id: str) -> List[str]:
        """Return ordered variant IDs for rendering a work document."""

    @abstractmethod
    def get_work_personal_remedial_variant_ids(
        self,
        work_id: str,
    ) -> List[str]:
        """Return ordered remedial variant IDs with a resolvable student."""

    @abstractmethod
    def get_variant_type(self, variant_id: str) -> Optional[str]:
        """Return variant type, or None when the variant does not exist."""

    @abstractmethod
    def get_remedial_sheet_source(
        self,
        variant_id: str,
    ) -> Optional[RemedialSheetSource]:
        """Return normalized remedial facts, or None when variant is missing."""
