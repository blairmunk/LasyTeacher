"""Build event review page data."""

from core_logic.entities.review import EventReviewData
from core_logic.interfaces.review_repo import IReviewRepository
from core_logic.services.review_service import ReviewService


class GetEventReviewUseCase:
    def __init__(
        self,
        review_repo: IReviewRepository,
        review_service: ReviewService,
    ):
        self.review_repo = review_repo
        self.review_service = review_service

    def execute(self, event_id: str) -> EventReviewData:
        return self.review_service.build_event_review(
            participations=self.review_repo.get_event_review_participations(event_id),
            available_variants=self.review_repo.get_available_variants(event_id),
        )
