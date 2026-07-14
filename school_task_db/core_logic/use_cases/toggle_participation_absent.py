"""Toggle a review participation absent status."""

from dataclasses import dataclass

from core_logic.entities.review import ReviewParticipationStatusChange
from core_logic.interfaces.review_repo import IReviewRepository


@dataclass(frozen=True)
class ToggleParticipationAbsentRequest:
    participation_id: str


class ToggleParticipationAbsentUseCase:
    def __init__(self, review_repo: IReviewRepository):
        self.review_repo = review_repo

    def execute(
        self,
        request: ToggleParticipationAbsentRequest,
    ) -> ReviewParticipationStatusChange:
        return self.review_repo.toggle_absent(request.participation_id)
