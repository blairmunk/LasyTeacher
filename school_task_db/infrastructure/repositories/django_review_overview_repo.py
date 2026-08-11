"""Django read adapter for review overview screens."""

from typing import List

from django.db.models import Count, Q

from core_logic.entities.review import (
    EventReviewParticipationRow,
    ReviewEventProgress,
    ReviewVariantRef,
)
from core_logic.interfaces.review_overview_repo import IReviewOverviewRepository
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_review_queries import (
    variant_task_counts,
)
from infrastructure.repositories.django_review_refs import (
    review_event_ref,
    review_mark_ref,
    review_participation_ref,
    review_student_ref,
    review_variant_ref,
)
from works.models import Variant


class DjangoReviewOverviewRepository(IReviewOverviewRepository):
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
        task_counts = variant_task_counts(
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
        task_counts = variant_task_counts([variant.pk for variant in variants])
        return [
            review_variant_ref(variant, task_counts=task_counts)
            for variant in variants
        ]
