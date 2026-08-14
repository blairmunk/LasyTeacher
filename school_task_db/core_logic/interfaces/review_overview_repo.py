"""Read port for review dashboard and event overview screens."""

from abc import ABC, abstractmethod

from core_logic.entities.review import (
    EventReviewParticipationRow,
    ReviewEventProgress,
    ReviewVariantRef,
)


class IReviewOverviewRepository(ABC):
    @abstractmethod
    def get_dashboard_events(self) -> tuple[ReviewEventProgress, ...]:
        """Return event progress rows for the review dashboard."""

    @abstractmethod
    def get_event_review_participations(
        self,
        event_id: str,
    ) -> tuple[EventReviewParticipationRow, ...]:
        """Return participation rows for event review."""

    @abstractmethod
    def get_available_variants(self, event_id: str) -> tuple[ReviewVariantRef, ...]:
        """Return variants that can be assigned during event review."""
