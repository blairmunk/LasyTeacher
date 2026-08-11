"""Repository interface for event participation commands."""

from abc import ABC, abstractmethod
from typing import Dict, List

from core_logic.entities.event import EventVariantAssignmentResult


class IEventParticipationRepository(ABC):
    @abstractmethod
    def add_participants(self, event_id: str, student_ids: List[str]) -> int:
        """Add assigned participations and return the number created."""

    @abstractmethod
    def assign_variants(
        self,
        event_id: str,
        assignments: Dict[str, str],
    ) -> int:
        """Assign variants and return the number changed."""

    @abstractmethod
    def assign_variant(
        self,
        event_id: str,
        participation_id: str,
        variant_id: str,
    ) -> EventVariantAssignmentResult:
        """Assign one variant and return user-feedback data."""

    @abstractmethod
    def create_participation(
        self,
        event_id: str,
        student_id: str,
        variant_id: str,
    ) -> str:
        """Create an assigned participation and return its ID."""
