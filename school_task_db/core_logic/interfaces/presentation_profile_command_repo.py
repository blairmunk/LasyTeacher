"""Command repository port for document presentation profiles."""

from abc import ABC, abstractmethod

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    UpdatePresentationProfileParams,
)


class IPresentationProfileCommandRepository(ABC):
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
