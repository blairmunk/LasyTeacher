"""Django repository for event read models."""

from typing import Optional

from django.db.models import Count

from core_logic.entities.event import (
    CourseSummary,
    EventEntity,
    EventListItem,
    EventMarkRef,
    EventParticipationRef,
    EventParticipationRow,
    EventStudentRef,
    EventVariantRef,
    EventWorkScanRef,
    WorkSummary,
)
from core_logic.interfaces.event_read_repo import IEventReadRepository
from events.models import Event, EventParticipation, Mark
from students.models import StudentGroup
from works.models import Variant


class DjangoEventReadRepository(IEventReadRepository):
    def get_list_events(self):
        return [
            EventListItem(
                pk=str(event.pk),
                name=event.name,
                status=event.status,
                status_display=event.get_status_display(),
                planned_date=event.planned_date,
                participant_count=event.participant_count,
                work=WorkSummary(
                    id=str(event.work.pk),
                    name=event.work.name,
                    work_type=event.work.work_type,
                    work_type_display=event.work.get_work_type_display(),
                    assessment_mode=event.work.assessment_mode,
                ) if event.work else None,
                course=CourseSummary(
                    pk=str(event.course.pk),
                    name=event.course.name,
                ) if event.course else None,
            )
            for event in Event.objects.select_related(
                'work',
                'course',
            ).annotate(
                participant_count=Count('eventparticipation'),
            ).order_by('-planned_date')
        ]

    def get_detail_participations(self, event_id: str):
        participations = EventParticipation.objects.filter(
            event_id=event_id,
        ).select_related(
            'student',
            'variant',
        ).order_by('student__last_name', 'student__first_name')

        marks = {
            mark.participation_id: mark
            for mark in Mark.objects.filter(
                participation_id__in=[p.pk for p in participations]
            )
        }
        return [
            EventParticipationRow(
                pk=str(participation.pk),
                status=participation.status,
                student=EventStudentRef(
                    pk=str(participation.student.pk),
                    last_name=participation.student.last_name,
                    first_name=participation.student.first_name,
                    middle_name=participation.student.middle_name,
                ),
                variant=(
                    EventVariantRef(
                        pk=str(participation.variant.pk),
                        number=participation.variant.number,
                    )
                    if participation.variant
                    else None
                ),
                mark_obj=(
                    self._event_mark_ref(marks[participation.pk])
                    if participation.pk in marks
                    else None
                ),
            )
            for participation in participations
        ]

    def get_available_variants(self, event_id: str):
        event = Event.objects.select_related('work').filter(pk=event_id).first()
        if not event or not event.work_id:
            return []
        return [
            EventVariantRef(pk=str(variant.pk), number=variant.number)
            for variant in Variant.objects.filter(work=event.work).order_by('number')
        ]

    def get_event_status(self, event_id: str) -> Optional[str]:
        return Event.objects.filter(pk=event_id).values_list(
            'status',
            flat=True,
        ).first()

    def get_by_id(self, event_id: str) -> Optional[EventEntity]:
        event = Event.objects.select_related('work', 'course').filter(
            pk=event_id
        ).first()
        if not event:
            return None

        participant_group_names = ', '.join(
            StudentGroup.objects.filter(
                students__eventparticipation__event_id=event_id,
            ).distinct().order_by('name').values_list('name', flat=True)
        )
        return EventEntity(
            id=str(event.pk),
            name=event.name,
            work_id=str(event.work_id),
            work_name=event.work.name,
            status=event.status,
            status_display=event.get_status_display(),
            course_id=str(event.course_id) if event.course_id else None,
            course_name=event.course.name if event.course else '',
            planned_date=event.planned_date,
            location=event.location,
            description=event.description,
            short_uuid=event.get_short_uuid(),
            work_type=event.work.work_type,
            work_type_display=event.work.get_work_type_display(),
            work_variant_count=event.work.variant_set.count(),
            participant_group_names=participant_group_names,
            work_assessment_mode=event.work.assessment_mode,
        )

    def get_participation_ref(self, participation_id: str):
        participation = EventParticipation.objects.filter(
            pk=participation_id,
        ).first()
        if not participation:
            return None
        return EventParticipationRef(
            id=str(participation.pk),
            event_id=str(participation.event_id),
        )

    @staticmethod
    def _event_mark_ref(mark: Mark) -> EventMarkRef:
        work_scan = None
        if mark.work_scan:
            work_scan = EventWorkScanRef(url=mark.work_scan.url)
        return EventMarkRef(score=mark.score, work_scan=work_scan)
