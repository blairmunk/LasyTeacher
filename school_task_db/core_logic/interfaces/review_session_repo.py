"""Persistence port for reviewer session progress."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.review import ReviewSessionRef


class IReviewSessionRepository(ABC):
    @abstractmethod
    def get_recent_sessions(
        self,
        reviewer_id: str,
        limit: int = 5,
    ) -> List[ReviewSessionRef]:
        """Return recent review sessions for a reviewer."""

    @abstractmethod
    def sync_review_session(
        self,
        reviewer_id: str,
        event_id: str,
        total_participations: int,
        checked_participations: int,
    ) -> ReviewSessionRef:
        """Create or update a review session progress row."""

