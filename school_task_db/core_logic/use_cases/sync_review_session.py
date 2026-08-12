"""Create or update review session progress."""

from dataclasses import dataclass

from core_logic.entities.review import ReviewSessionRef
from core_logic.interfaces.review_session_command_repo import (
    IReviewSessionCommandRepository,
)


@dataclass(frozen=True)
class SyncReviewSessionRequest:
    reviewer_id: str
    event_id: str
    total_participations: int
    checked_participations: int


class SyncReviewSessionUseCase:
    def __init__(self, session_repo: IReviewSessionCommandRepository):
        self.session_repo = session_repo

    def execute(self, request: SyncReviewSessionRequest) -> ReviewSessionRef:
        return self.session_repo.sync_review_session(
            reviewer_id=request.reviewer_id,
            event_id=request.event_id,
            total_participations=request.total_participations,
            checked_participations=request.checked_participations,
        )
