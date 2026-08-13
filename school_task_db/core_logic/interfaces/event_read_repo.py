"""Repository interface for event read models."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.event import (
    EventEntity,
    EventListItem,
    EventParticipationRef,
    EventParticipationRow,
    EventVariantRef,
)


class IEventReadRepository(ABC):
    @abstractmethod
    def get_list_events(self) -> tuple[EventListItem, ...]:
        """Return events for the list page."""

    @abstractmethod
    def get_detail_participations(
        self,
        event_id: str,
    ) -> tuple[EventParticipationRow, ...]:
        """Return event detail participation rows."""

    @abstractmethod
    def get_available_variants(
        self,
        event_id: str,
    ) -> tuple[EventVariantRef, ...]:
        """Return variants available for assignment."""

    @abstractmethod
    def get_event_status(self, event_id: str) -> Optional[str]:
        """Return the current event status."""

    @abstractmethod
    def get_by_id(self, event_id: str) -> Optional[EventEntity]:
        """Return an event by ID."""

    @abstractmethod
    def get_participation_ref(
        self,
        participation_id: str,
    ) -> Optional[EventParticipationRef]:
        """Return a lightweight participation reference by ID."""
