"""Read-only persistence port for reviewer sessions."""

from abc import ABC, abstractmethod

from core_logic.entities.review import ReviewSessionRef


class IReviewSessionQueryRepository(ABC):
    @abstractmethod
    def get_recent_sessions(
        self,
        reviewer_id: str,
        limit: int = 5,
    ) -> tuple[ReviewSessionRef, ...]:
        """Return recent review sessions for a reviewer."""
