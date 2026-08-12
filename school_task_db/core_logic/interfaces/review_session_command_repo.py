"""Command persistence port for reviewer session progress."""

from abc import ABC, abstractmethod

from core_logic.entities.review import ReviewSessionRef


class IReviewSessionCommandRepository(ABC):
    @abstractmethod
    def sync_review_session(
        self,
        reviewer_id: str,
        event_id: str,
        total_participations: int,
        checked_participations: int,
    ) -> ReviewSessionRef:
        """Create or update a review session progress row."""
