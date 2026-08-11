"""Django adapter for the participation review workflow."""

from typing import List, Optional

from core_logic.entities.review import (
    ReviewCommentRef,
    ReviewEventRef,
    ReviewMarkRef,
    ReviewParticipationAbsenceContext,
    ReviewParticipationRef,
    ReviewSaveNavigation,
)
from core_logic.interfaces.review_workflow_repo import IReviewWorkflowRepository
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_review_queries import (
    variant_task_counts,
)
from infrastructure.repositories.django_review_refs import (
    review_event_ref,
    review_mark_ref,
    review_participation_ref,
)
from review.models import ReviewComment


class DjangoReviewWorkflowRepository(IReviewWorkflowRepository):
    def get_participation(self, participation_id: str) -> ReviewParticipationRef:
        participation = EventParticipation.objects.select_related(
            'student',
            'variant',
            'event',
            'event__work',
        ).get(pk=participation_id)
        return review_participation_ref(participation)

    def get_or_create_mark(
        self,
        participation_id: str,
        default_max_points: Optional[int],
    ) -> ReviewMarkRef:
        mark, _ = Mark.objects.get_or_create(
            participation_id=participation_id,
            defaults={'max_points': default_max_points},
        )
        return review_mark_ref(mark)

    def get_review_participations(
        self,
        event_id: str,
    ) -> List[ReviewParticipationRef]:
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
        task_counts = variant_task_counts(
            [p.variant_id for p in participations if p.variant_id]
        )
        return [
            review_participation_ref(participation, task_counts=task_counts)
            for participation in participations
        ]

    def get_typical_comments(self, limit: int = 10) -> List[ReviewCommentRef]:
        return [
            ReviewCommentRef(text=comment.text)
            for comment in ReviewComment.objects.filter(
                is_active=True,
            ).order_by('-usage_count')[:limit]
        ]

    def finalize_event(self, event_id: str) -> ReviewEventRef:
        event = Event.objects.select_related('work', 'course').get(pk=event_id)
        event.status = 'graded'
        event.save()
        return review_event_ref(event)

    def get_participation_absence_context(
        self,
        participation_id: str,
    ) -> ReviewParticipationAbsenceContext:
        participation = EventParticipation.objects.select_related(
            'student',
            'event',
        ).get(pk=participation_id)
        return ReviewParticipationAbsenceContext(
            participation_id=str(participation.pk),
            event_id=str(participation.event.pk),
            student_last_name=participation.student.last_name,
            status=participation.status,
            has_checked_result=Mark.objects.filter(
                participation=participation,
                score__isnull=False,
            ).exists(),
        )

    def set_participation_status(
        self,
        participation_id: str,
        status: str,
    ) -> None:
        EventParticipation.objects.filter(pk=participation_id).update(
            status=status,
        )

    def get_save_navigation(self, participation_id: str) -> ReviewSaveNavigation:
        participation = EventParticipation.objects.select_related('event').get(
            pk=participation_id,
        )
        participations = list(
            EventParticipation.objects.filter(
                event=participation.event,
            ).exclude(
                status='absent',
            ).select_related(
                'student',
                'event',
                'variant',
            ).order_by('student__last_name', 'student__first_name')
        )

        current_index = self._participation_index(
            participations=participations,
            participation_id=participation_id,
        )
        next_participation = self._next_ungraded_participation(
            participations=participations,
            current_index=current_index,
        )
        if next_participation is None and current_index + 1 < len(participations):
            next_participation = participations[current_index + 1]

        return ReviewSaveNavigation(
            event_id=str(participation.event.pk),
            next_participation=(
                review_participation_ref(next_participation)
                if next_participation
                else None
            ),
            all_checked=next_participation is None,
        )

    @staticmethod
    def _participation_index(participations, participation_id: str) -> int:
        try:
            return next(
                index
                for index, participation in enumerate(participations)
                if str(participation.pk) == str(participation_id)
            )
        except StopIteration:
            return -1

    @staticmethod
    def _next_ungraded_participation(participations, current_index: int):
        start_index = 0 if current_index < 0 else current_index + 1
        participation_ids = [
            participation.pk
            for participation in participations[start_index:]
        ]
        graded_ids = set(
            Mark.objects.filter(
                participation_id__in=participation_ids,
                score__isnull=False,
            ).values_list('participation_id', flat=True)
        )
        for participation in participations[start_index:]:
            if participation.pk not in graded_ids:
                return participation
        return None
