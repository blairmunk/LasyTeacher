"""Django implementation of the review repository."""

from typing import List

from django.db.models import Count, Q

from core_logic.entities.review import (
    EventReviewParticipationRow,
    ReviewCommentRef,
    ReviewEventRef,
    ReviewEventProgress,
    ReviewMarkRef,
    ReviewParticipationAbsenceContext,
    ReviewParticipationRef,
    ReviewSaveNavigation,
    ReviewVariantRef,
)
from core_logic.interfaces.review_repo import IReviewRepository
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_review_refs import (
    review_event_ref,
    review_mark_ref,
    review_participation_ref,
    review_student_ref,
    review_variant_ref,
)
from review.models import ReviewComment
from works.models import Variant, VariantTask


class DjangoReviewRepository(IReviewRepository):
    def get_dashboard_events(self) -> List[ReviewEventProgress]:
        events = Event.objects.annotate(
            total_participants=Count('eventparticipation'),
            graded_participants=Count(
                'eventparticipation',
                filter=Q(eventparticipation__status='graded'),
            ),
            absent_participants=Count(
                'eventparticipation',
                filter=Q(eventparticipation__status='absent'),
            ),
        ).filter(
            total_participants__gt=0,
        ).select_related(
            'work',
            'course',
        ).order_by('-planned_date')

        result = []
        for event in events:
            active = event.total_participants - event.absent_participants
            progress = (
                round(event.graded_participants / active * 100, 1)
                if active > 0
                else 100.0
            )
            result.append(
                ReviewEventProgress(
                    event=review_event_ref(event),
                    total_participants=event.total_participants,
                    graded_participants=event.graded_participants,
                    absent_participants=event.absent_participants,
                    active_participants=active,
                    progress_percentage=progress,
                    remaining=active - event.graded_participants,
                )
            )
        return result

    def get_event_review_participations(
        self,
        event_id: str,
    ) -> List[EventReviewParticipationRow]:
        participations = EventParticipation.objects.filter(
            event_id=event_id,
        ).select_related(
            'student',
            'variant',
            'event',
        ).order_by('student__last_name', 'student__first_name')

        marks = {
            mark.participation_id: mark
            for mark in Mark.objects.filter(
                participation_id__in=[p.pk for p in participations]
            )
        }
        task_counts = self._variant_task_counts(
            [p.variant_id for p in participations if p.variant_id]
        )

        result = []
        for participation in participations:
            mark = marks.get(participation.pk)
            mark_ref = review_mark_ref(mark) if mark else None
            result.append(
                EventReviewParticipationRow(
                    participation=review_participation_ref(
                        participation,
                        task_counts=task_counts,
                    ),
                    mark=mark_ref,
                    has_mark=mark is not None and mark.score is not None,
                    is_absent=participation.status == 'absent',
                    student=review_student_ref(participation.student),
                    variant=(
                        review_variant_ref(
                            participation.variant,
                            task_counts=task_counts,
                        )
                        if participation.variant
                        else None
                    ),
                )
            )
        return result

    def get_available_variants(self, event_id: str) -> List[ReviewVariantRef]:
        event = Event.objects.select_related('work').filter(pk=event_id).first()
        if not event or not event.work_id:
            return []

        variants = Variant.objects.filter(work=event.work).order_by('number')
        task_counts = self._variant_task_counts([variant.pk for variant in variants])
        return [
            review_variant_ref(variant, task_counts=task_counts)
            for variant in variants
        ]

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
        default_max_points: int,
    ) -> ReviewMarkRef:
        mark, _ = Mark.objects.get_or_create(
            participation_id=participation_id,
            defaults={'max_points': default_max_points},
        )
        return review_mark_ref(mark)

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
        task_counts = self._variant_task_counts(
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

    def _variant_task_counts(self, variant_ids) -> dict:
        variant_ids = [variant_id for variant_id in variant_ids if variant_id]
        if not variant_ids:
            return {}

        rows = VariantTask.objects.filter(
            variant_id__in=variant_ids,
        ).values('variant_id').annotate(total=Count('id'))
        return {row['variant_id']: row['total'] for row in rows}

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
        if current_index < 0:
            start_index = 0
        else:
            start_index = current_index + 1

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
