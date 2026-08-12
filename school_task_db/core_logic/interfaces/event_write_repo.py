"""Repository interface for event write operations."""

from abc import ABC, abstractmethod

from core_logic.entities.event_commands import CreateEventParams


class IEventWriteRepository(ABC):
    @abstractmethod
    def create_event(self, params: CreateEventParams) -> str:
        """Create an event and return its ID."""

    @abstractmethod
    def update_event(self, params: CreateEventParams) -> bool:
        """Update an event and return whether it was found."""

    @abstractmethod
    def set_event_status(self, event_id: str, status: str) -> None:
        """Persist a new event status."""
