"""Finalize review for an event."""

from dataclasses import dataclass

from core_logic.entities.review import ReviewEventRef
from core_logic.interfaces.review_workflow_repo import IReviewWorkflowRepository


@dataclass(frozen=True)
class FinalizeReviewEventRequest:
    event_id: str


class FinalizeReviewEventUseCase:
    def __init__(self, review_repo: IReviewWorkflowRepository):
        self.review_repo = review_repo

    def execute(self, request: FinalizeReviewEventRequest) -> ReviewEventRef:
        return self.review_repo.finalize_event(request.event_id)
