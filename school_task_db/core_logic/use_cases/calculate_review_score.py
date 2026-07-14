"""Calculate the displayed score from points."""

from dataclasses import dataclass

from core_logic.entities.review import ReviewScoreCalculation
from core_logic.services.review_service import ReviewService


@dataclass(frozen=True)
class CalculateReviewScoreRequest:
    points: object = 0
    max_points: object = 1


class CalculateReviewScoreUseCase:
    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    def execute(
        self,
        request: CalculateReviewScoreRequest,
    ) -> ReviewScoreCalculation:
        return self.review_service.calculate_score(
            points=self._int_or_default(request.points, 0),
            max_points=self._int_or_default(request.max_points, 1),
        )

    @staticmethod
    def _int_or_default(value, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
