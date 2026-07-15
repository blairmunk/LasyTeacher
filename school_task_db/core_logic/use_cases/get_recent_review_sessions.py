"""Get recent review sessions for a reviewer."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.review import ReviewSessionRef
from core_logic.interfaces.review_repo import IReviewRepository


@dataclass(frozen=True)
class GetRecentReviewSessionsRequest:
    reviewer_id: str
    limit: int = 5


class GetRecentReviewSessionsUseCase:
    def __init__(self, review_repo: IReviewRepository):
        self.review_repo = review_repo

    def execute(
        self,
        request: GetRecentReviewSessionsRequest,
    ) -> List[ReviewSessionRef]:
        return self.review_repo.get_recent_sessions(
            reviewer_id=request.reviewer_id,
            limit=request.limit,
        )
