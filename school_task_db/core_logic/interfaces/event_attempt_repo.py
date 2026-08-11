"""Repository interface for checked event attempts."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.event import CheckedAttemptRef, ParticipationAttemptData


class IEventAttemptRepository(ABC):
    @abstractmethod
    def get_latest_student_attempt(
        self,
        event_id: str,
        student_id: str,
    ) -> Optional[CheckedAttemptRef]:
        """Return the latest captured attempt for a student and event."""

    @abstractmethod
    def get_participation_attempts(
        self,
        event_id: str,
    ) -> List[ParticipationAttemptData]:
        """Return participations with their latest captured attempts."""
