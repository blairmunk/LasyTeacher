"""Create or update review session progress."""

from dataclasses import dataclass

from core_logic.entities.review import ReviewSessionRef
from core_logic.interfaces.review_repo import IReviewRepository


@dataclass(frozen=True)
class SyncReviewSessionRequest:
    reviewer_id: str
    event_id: str
    total_participations: int
    checked_participations: int


class SyncReviewSessionUseCase:
    def __init__(self, review_repo: IReviewRepository):
        self.review_repo = review_repo

    def execute(self, request: SyncReviewSessionRequest) -> ReviewSessionRef:
        return self.review_repo.sync_review_session(
            reviewer_id=request.reviewer_id,
            event_id=request.event_id,
            total_participations=request.total_participations,
            checked_participations=request.checked_participations,
        )
