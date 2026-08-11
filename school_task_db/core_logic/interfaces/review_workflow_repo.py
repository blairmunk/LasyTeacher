"""Persistence port for the participation review workflow."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.review import (
    ReviewCommentRef,
    ReviewEventRef,
    ReviewMarkRef,
    ReviewParticipationAbsenceContext,
    ReviewParticipationRef,
    ReviewSaveNavigation,
)


class IReviewWorkflowRepository(ABC):
    @abstractmethod
    def get_participation(self, participation_id: str) -> ReviewParticipationRef:
        """Return participation details for the review screen."""

    @abstractmethod
    def get_or_create_mark(
        self,
        participation_id: str,
        default_max_points: Optional[int],
    ) -> ReviewMarkRef:
        """Return the existing mark or create one with default max points."""

    @abstractmethod
    def get_review_participations(
        self,
        event_id: str,
    ) -> List[ReviewParticipationRef]:
        """Return non-absent participations for review navigation."""

    @abstractmethod
    def get_typical_comments(self, limit: int = 10) -> List[ReviewCommentRef]:
        """Return active quick comments for the review form."""

    @abstractmethod
    def finalize_event(self, event_id: str) -> ReviewEventRef:
        """Mark an event as fully graded and return event details."""

    @abstractmethod
    def get_participation_absence_context(
        self,
        participation_id: str,
    ) -> ReviewParticipationAbsenceContext:
        """Return facts needed to decide an absence status change."""

    @abstractmethod
    def set_participation_status(
        self,
        participation_id: str,
        status: str,
    ) -> None:
        """Persist a participation status selected by the use case."""

    @abstractmethod
    def get_save_navigation(self, participation_id: str) -> ReviewSaveNavigation:
        """Return where the review screen should go after save-and-next."""
