"""Build event review page data."""

from core_logic.entities.review import EventReviewData
from core_logic.interfaces.event_repo import IEventRepository
from core_logic.interfaces.review_repo import IReviewRepository
from core_logic.services.review_service import ReviewService


class GetEventReviewUseCase:
    def __init__(
        self,
        event_repo: IEventRepository,
        review_repo: IReviewRepository,
        review_service: ReviewService,
    ):
        self.event_repo = event_repo
        self.review_repo = review_repo
        self.review_service = review_service

    def execute(self, event_id: str) -> EventReviewData:
        event = self.event_repo.get_by_id(event_id)
        if event is None:
            return EventReviewData()

        return self.review_service.build_event_review(
            event=event,
            participations=self.review_repo.get_event_review_participations(event_id),
            available_variants=self.review_repo.get_available_variants(event_id),
        )
