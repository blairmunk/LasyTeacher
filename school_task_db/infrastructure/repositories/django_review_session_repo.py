"""Django persistence adapter for reviewer sessions."""

from typing import List

from core_logic.entities.review import ReviewSessionRef
from core_logic.interfaces.review_session_repo import IReviewSessionRepository
from infrastructure.repositories.django_review_refs import review_session_ref
from review.models import ReviewSession


class DjangoReviewSessionRepository(IReviewSessionRepository):
    def get_recent_sessions(
        self,
        reviewer_id: str,
        limit: int = 5,
    ) -> List[ReviewSessionRef]:
        sessions = ReviewSession.objects.filter(
            reviewer_id=reviewer_id,
        ).select_related(
            'event',
            'event__work',
            'event__course',
        ).order_by('-started_at')[:limit]
        return [review_session_ref(session) for session in sessions]

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

