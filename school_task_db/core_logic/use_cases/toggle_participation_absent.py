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
        context = self.review_repo.get_participation_absence_context(
            request.participation_id,
        )
        if context.status != 'absent' and context.has_checked_result:
            return ReviewParticipationStatusChange(
                participation_id=context.participation_id,
                event_id=context.event_id,
                student_last_name=context.student_last_name,
                status=context.status,
                is_absent=False,
                changed=False,
                message='Проверенную работу нельзя отметить как пропущенную.',
            )

        if context.status == 'absent':
            new_status = 'graded' if context.has_checked_result else 'assigned'
        else:
            new_status = 'absent'
        self.review_repo.set_participation_status(
            context.participation_id,
            new_status,
        )
        return ReviewParticipationStatusChange(
            participation_id=context.participation_id,
            event_id=context.event_id,
            student_last_name=context.student_last_name,
            status=new_status,
            is_absent=new_status == 'absent',
        )
