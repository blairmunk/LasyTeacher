"""Build review dashboard data."""

from core_logic.entities.review import ReviewDashboardData
from core_logic.interfaces.review_repo import IReviewRepository
from core_logic.services.review_service import ReviewService


class GetReviewDashboardUseCase:
    def __init__(
        self,
        review_repo: IReviewRepository,
        review_service: ReviewService,
    ):
        self.review_repo = review_repo
        self.review_service = review_service

    def execute(self) -> ReviewDashboardData:
        return self.review_service.build_dashboard(
            self.review_repo.get_dashboard_events(),
        )
