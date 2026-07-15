"""Prepare participation review form data for saving."""

from dataclasses import dataclass
from typing import Mapping

from core_logic.entities.review import ReviewSubmissionData
from core_logic.services.review_service import ReviewService


@dataclass(frozen=True)
class PrepareParticipationReviewSubmissionRequest:
    data: Mapping[str, object]


class PrepareParticipationReviewSubmissionUseCase:
    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    def execute(
        self,
        request: PrepareParticipationReviewSubmissionRequest,
    ) -> ReviewSubmissionData:
        return self.review_service.parse_submission(request.data)
