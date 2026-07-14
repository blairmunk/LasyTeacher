"""Review repository interface."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.review import (
    EventReviewParticipationRow,
    ReviewCommentRef,
    ReviewEventProgress,
    ReviewMarkRef,
    ReviewParticipationRef,
    ReviewVariantRef,
    ReviewVariantTaskRef,
)


class IReviewRepository(ABC):
    @abstractmethod
    def get_dashboard_events(self) -> List[ReviewEventProgress]:
        """Return event progress rows for the review dashboard."""

    @abstractmethod
    def get_event_review_participations(
        self,
        event_id: str,
    ) -> List[EventReviewParticipationRow]:
        """Return participation rows for event review."""

    @abstractmethod
    def get_available_variants(self, event_id: str) -> List[ReviewVariantRef]:
        """Return variants that can be assigned during event review."""

    @abstractmethod
    def get_participation(self, participation_id: str) -> ReviewParticipationRef:
        """Return participation details for the review screen."""

    @abstractmethod
    def get_variant_tasks(self, participation_id: str) -> List[ReviewVariantTaskRef]:
        """Return ordered variant tasks with scoring weights."""

    @abstractmethod
    def get_or_create_mark(
        self,
        participation_id: str,
        default_max_points: int,
    ) -> ReviewMarkRef:
        """Return the existing mark or create one with default max points."""

    @abstractmethod
    def get_review_participations(self, event_id: str) -> List[ReviewParticipationRef]:
        """Return non-absent participations ordered for review navigation."""

    @abstractmethod
    def get_typical_comments(self, limit: int = 10) -> List[ReviewCommentRef]:
        """Return active quick comments for the review form."""
