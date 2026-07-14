"""Django implementation of the review repository."""

from typing import List

from core_logic.entities.review import (
    ReviewCommentRef,
    ReviewEventRef,
    ReviewMarkRef,
    ReviewParticipationRef,
    ReviewStudentRef,
    ReviewTaskRef,
    ReviewTopicRef,
    ReviewVariantRef,
    ReviewVariantTaskRef,
    ReviewWorkScanRef,
)
from core_logic.interfaces.review_repo import IReviewRepository
from events.models import EventParticipation, Mark
from review.models import ReviewComment
from works.models import VariantTask


class DjangoReviewRepository(IReviewRepository):
    def get_participation(self, participation_id: str) -> ReviewParticipationRef:
        participation = EventParticipation.objects.select_related(
            'student',
            'variant',
            'event',
            'event__work',
        ).get(pk=participation_id)
        return self._participation_ref(participation)

    def get_variant_tasks(self, participation_id: str) -> List[ReviewVariantTaskRef]:
        participation = EventParticipation.objects.select_related(
            'variant',
        ).get(pk=participation_id)
        if not participation.variant:
            return []

        variant_tasks = VariantTask.objects.filter(
            variant=participation.variant,
        ).select_related(
            'task',
            'task__topic',
        ).order_by('order')

        return [
            ReviewVariantTaskRef(
                task=ReviewTaskRef(
                    id=str(variant_task.task.pk),
                    text=variant_task.task.text,
                    answer=variant_task.task.answer,
                    short_solution=variant_task.task.short_solution,
                    difficulty=variant_task.task.difficulty,
                    topic=(
                        ReviewTopicRef(
                            pk=str(variant_task.task.topic.pk),
                            name=variant_task.task.topic.name,
                        )
                        if variant_task.task.topic
                        else None
                    ),
                ),
                weight=variant_task.weight,
            )
            for variant_task in variant_tasks
        ]

    def get_or_create_mark(
        self,
        participation_id: str,
        default_max_points: int,
    ) -> ReviewMarkRef:
        mark, _ = Mark.objects.get_or_create(
            participation_id=participation_id,
            defaults={'max_points': default_max_points},
        )
        return self._mark_ref(mark)

    def get_review_participations(self, event_id: str) -> List[ReviewParticipationRef]:
        participations = EventParticipation.objects.filter(
            event_id=event_id,
        ).exclude(
            status='absent',
        ).select_related(
            'student',
            'variant',
            'event',
        ).order_by(
            'student__last_name',
            'student__first_name',
        )
        return [self._participation_ref(participation) for participation in participations]

    def get_typical_comments(self, limit: int = 10) -> List[ReviewCommentRef]:
        return [
            ReviewCommentRef(text=comment.text)
            for comment in ReviewComment.objects.filter(
                is_active=True,
            ).order_by('-usage_count')[:limit]
        ]

    def _participation_ref(self, participation) -> ReviewParticipationRef:
        student = participation.student
        event = participation.event
        variant = participation.variant
        return ReviewParticipationRef(
            pk=str(participation.pk),
            student=ReviewStudentRef(
                pk=str(student.pk),
                last_name=student.last_name,
                first_name=student.first_name,
                middle_name=student.middle_name,
            ),
            event=ReviewEventRef(
                pk=str(event.pk),
                name=event.name,
            ),
            variant=(
                ReviewVariantRef(
                    pk=str(variant.pk),
                    number=variant.number,
                )
                if variant
                else None
            ),
        )

    def _mark_ref(self, mark: Mark) -> ReviewMarkRef:
        work_scan = None
        if mark.work_scan:
            work_scan = ReviewWorkScanRef(
                name=mark.work_scan.name,
                url=mark.work_scan.url,
            )

        return ReviewMarkRef(
            pk=str(mark.pk),
            score=mark.score,
            points=mark.points,
            max_points=mark.max_points,
            teacher_comment=mark.teacher_comment,
            work_scan=work_scan,
            task_scores=mark.task_scores or {},
        )
