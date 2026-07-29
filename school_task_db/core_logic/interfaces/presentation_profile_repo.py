"""Repository interface for document presentation profiles."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    DocumentPresentationProfile,
    UpdatePresentationProfileParams,
)


class IPresentationProfileRepository(ABC):
    @abstractmethod
    def list_presentation_profiles(
        self,
        document_type: str = '',
    ) -> List[DocumentPresentationProfile]:
        """Return profiles, optionally filtered by document type."""

    @abstractmethod
    def get_presentation_profile(
        self,
        presentation_profile_id: str,
        document_type: str = '',
    ) -> Optional[DocumentPresentationProfile]:
        """Return a profile by id, optionally constrained by type."""

    @abstractmethod
    def create_presentation_profile(
        self,
        params: CreatePresentationProfileParams,
    ) -> str:
        """Create a presentation profile and return its id."""

    @abstractmethod
    def update_presentation_profile(
        self,
        params: UpdatePresentationProfileParams,
    ) -> bool:
        """Update a presentation profile and report whether it existed."""
