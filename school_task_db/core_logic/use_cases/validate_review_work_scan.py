"""Validate an uploaded work scan before saving review results."""

from dataclasses import dataclass

from core_logic.entities.review import ReviewFileValidationResult
from core_logic.services.review_service import ReviewService


@dataclass(frozen=True)
class ValidateReviewWorkScanRequest:
    size: int
    content_type: str


class ValidateReviewWorkScanUseCase:
    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    def execute(
        self,
        request: ValidateReviewWorkScanRequest,
    ) -> ReviewFileValidationResult:
        return self.review_service.validate_work_scan(
            size=request.size,
            content_type=request.content_type,
        )
