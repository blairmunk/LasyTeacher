"""Django read adapter for reviewer sessions."""

from core_logic.entities.review import ReviewSessionRef
from core_logic.interfaces.review_session_query_repo import (
    IReviewSessionQueryRepository,
)
from infrastructure.repositories.django_review_refs import review_session_ref
from review.models import ReviewSession


class DjangoReviewSessionQueryRepository(IReviewSessionQueryRepository):
    def get_recent_sessions(
        self,
        reviewer_id: str,
        limit: int = 5,
    ) -> tuple[ReviewSessionRef, ...]:
        sessions = ReviewSession.objects.filter(
            reviewer_id=reviewer_id,
        ).select_related(
            'event',
            'event__work',
            'event__course',
        ).order_by('-started_at')[:limit]
        return tuple(review_session_ref(session) for session in sessions)
