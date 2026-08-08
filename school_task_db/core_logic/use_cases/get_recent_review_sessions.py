"""Get recent review sessions for a reviewer."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.review import ReviewSessionRef
from core_logic.interfaces.review_session_repo import IReviewSessionRepository


@dataclass(frozen=True)
class GetRecentReviewSessionsRequest:
    reviewer_id: str
    limit: int = 5


class GetRecentReviewSessionsUseCase:
    def __init__(self, session_repo: IReviewSessionRepository):
        self.session_repo = session_repo

    def execute(
        self,
        request: GetRecentReviewSessionsRequest,
    ) -> List[ReviewSessionRef]:
        return self.session_repo.get_recent_sessions(
            reviewer_id=request.reviewer_id,
            limit=request.limit,
        )
