"""Build data for checking a student's work."""

from core_logic.entities.review import ParticipationReviewData
from core_logic.interfaces.review_repo import IReviewRepository
from core_logic.services.review_service import ReviewService


class GetParticipationReviewUseCase:
    def __init__(
        self,
        review_repo: IReviewRepository,
        review_service: ReviewService,
    ):
        self.review_repo = review_repo
        self.review_service = review_service

    def execute(self, participation_id: str) -> ParticipationReviewData:
        participation = self.review_repo.get_participation(participation_id)
        variant_tasks = self.review_repo.get_variant_tasks(participation_id)
        assessable_variant_tasks = self.review_service.assessable_variant_tasks(
            variant_tasks,
        )
        mark = self.review_repo.get_or_create_mark(
            participation_id=participation_id,
            default_max_points=sum(
                task.weight
                for task in assessable_variant_tasks
            ),
        )
        review_participations = self.review_repo.get_review_participations(
            participation.event.pk,
        )
        navigation = self.review_service.build_navigation(
            participations=review_participations,
            current_participation_id=participation_id,
        )

        return ParticipationReviewData(
            participation=participation,
            mark=mark,
            tasks_with_scores=self.review_service.build_task_score_rows(
                variant_tasks=assessable_variant_tasks,
                existing_scores=mark.task_scores,
            ),
            typical_comments=self.review_repo.get_typical_comments(limit=10),
            previous_participation=navigation.previous_participation,
            next_participation=navigation.next_participation,
            current_position=navigation.current_position,
            total_positions=navigation.total_positions,
            navigation_progress=navigation.navigation_progress,
        )
