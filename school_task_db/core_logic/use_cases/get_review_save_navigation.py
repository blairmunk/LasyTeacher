"""Choose navigation after saving a reviewed participation."""

from dataclasses import dataclass

from core_logic.entities.review import ReviewSaveNavigation
from core_logic.interfaces.review_workflow_repo import IReviewWorkflowRepository


@dataclass(frozen=True)
class GetReviewSaveNavigationRequest:
    participation_id: str


class GetReviewSaveNavigationUseCase:
    def __init__(self, review_repo: IReviewWorkflowRepository):
        self.review_repo = review_repo

    def execute(
        self,
        request: GetReviewSaveNavigationRequest,
    ) -> ReviewSaveNavigation:
        return self.review_repo.get_save_navigation(request.participation_id)
