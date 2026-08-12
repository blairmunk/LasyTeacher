"""Django command adapter for reviewer session progress."""

from core_logic.entities.review import ReviewSessionRef
from core_logic.interfaces.review_session_command_repo import (
    IReviewSessionCommandRepository,
)
from infrastructure.repositories.django_review_refs import review_session_ref
from review.models import ReviewSession


class DjangoReviewSessionCommandRepository(IReviewSessionCommandRepository):
    def sync_review_session(
        self,
        reviewer_id: str,
        event_id: str,
        total_participations: int,
        checked_participations: int,
    ) -> ReviewSessionRef:
        session, _ = ReviewSession.objects.select_related(
            'event',
            'event__work',
            'event__course',
        ).get_or_create(
            reviewer_id=reviewer_id,
            event_id=event_id,
            defaults={
                'total_participations': total_participations,
                'checked_participations': checked_participations,
            },
        )
        session.total_participations = total_participations
        session.checked_participations = checked_participations
        session.save()
        return review_session_ref(session)
