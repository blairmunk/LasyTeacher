"""Read-only repository port for document presentation profiles."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.document import DocumentPresentationProfile


class IPresentationProfileCatalogRepository(ABC):
    @abstractmethod
    def list_presentation_profiles(
        self,
        document_type: str = '',
    ) -> tuple[DocumentPresentationProfile, ...]:
        """Return profiles, optionally filtered by document type."""

    @abstractmethod
    def get_presentation_profile(
        self,
        presentation_profile_id: str,
        document_type: str = '',
    ) -> Optional[DocumentPresentationProfile]:
        """Return a profile by id, optionally constrained by type."""
