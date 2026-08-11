"""Django implementation of the event repository."""

import datetime as dt
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from core_logic.entities.event import (
    CourseSummary,
    EventEntity,
    EventListItem,
    EventMarkRef,
    EventParticipationRef,
    EventParticipationRow,
    EventStudentRef,
    EventVariantAssignmentResult,
    EventVariantRef,
    EventWorkScanRef,
    WorkSummary,
)
from core_logic.interfaces.event_participation_repo import (
    IEventParticipationRepository,
)
from core_logic.interfaces.event_read_repo import IEventReadRepository
from core_logic.interfaces.event_repo import CreateEventParams
from core_logic.interfaces.event_write_repo import IEventWriteRepository
from events.models import Event, EventParticipation, Mark
from students.models import StudentGroup
from works.models import Variant


class DjangoEventRepository(
    IEventReadRepository,
    IEventWriteRepository,
    IEventParticipationRepository,
):
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

        rows = []
        for participation in participations:
            mark = marks.get(participation.pk)
            rows.append(
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
                    mark_obj=self._event_mark_ref(mark) if mark else None,
                )
            )
        return rows

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

    def add_participants(self, event_id: str, student_ids: List[str]) -> int:
        created_count = 0
        with transaction.atomic():
            for student_id in student_ids:
                _, created = EventParticipation.objects.get_or_create(
                    event_id=event_id,
                    student_id=student_id,
                    defaults={'status': 'assigned'},
                )
                if created:
                    created_count += 1
        return created_count

    def assign_variants(
        self,
        event_id: str,
        assignments: Dict[str, str],
    ) -> int:
        assigned_count = 0
        with transaction.atomic():
            participations = EventParticipation.objects.filter(
                event_id=event_id,
                pk__in=assignments.keys(),
            )
            for participation in participations:
                variant_id = assignments.get(str(participation.pk))
                if not variant_id:
                    continue
                participation.variant_id = variant_id
                participation.save()
                assigned_count += 1
        return assigned_count

    def assign_variant(
        self,
        event_id: str,
        participation_id: str,
        variant_id: str,
    ) -> EventVariantAssignmentResult:
        participation = EventParticipation.objects.select_related(
            'student',
        ).get(pk=participation_id, event_id=event_id)
        variant = Variant.objects.get(pk=variant_id)

        participation.variant = variant
        participation.save()

        return EventVariantAssignmentResult(
            variant_number=variant.number,
            student_last_name=participation.student.last_name,
            student_first_name=participation.student.first_name,
        )

    def set_event_status(self, event_id: str, status: str) -> None:
        Event.objects.filter(pk=event_id).update(status=status)

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

    def create_event(self, params: CreateEventParams) -> str:
        planned_date = self._parse_planned_date(params.date)
        event = Event.objects.create(
            name=params.name,
            work_id=params.work_id,
            planned_date=planned_date,
            status=params.status,
            course_id=params.course_id,
            location=params.location,
            description=params.description,
        )
        return str(event.pk)

    def update_event(self, params: CreateEventParams) -> bool:
        event = Event.objects.filter(pk=params.event_id).first()
        if event is None:
            return False

        event.name = params.name
        event.work_id = params.work_id
        event.planned_date = self._parse_planned_date(params.date)
        event.status = params.status
        event.course_id = params.course_id
        event.location = params.location
        event.description = params.description
        event.save()
        return True

    def create_participation(
        self,
        event_id: str,
        student_id: str,
        variant_id: str,
    ) -> str:
        participation = EventParticipation.objects.create(
            event_id=event_id,
            student_id=student_id,
            variant_id=variant_id,
            status='assigned',
        )
        return str(participation.pk)

    def _event_mark_ref(self, mark: Mark) -> EventMarkRef:
        work_scan = None
        if mark.work_scan:
            work_scan = EventWorkScanRef(url=mark.work_scan.url)
        return EventMarkRef(score=mark.score, work_scan=work_scan)

    @staticmethod
    def _parse_planned_date(date_value: Optional[Any]):
        if isinstance(date_value, dt.datetime):
            if timezone.is_naive(date_value):
                return timezone.make_aware(date_value)
            return date_value

        if isinstance(date_value, dt.date):
            date_obj = date_value
        elif date_value:
            try:
                date_obj = dt.datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                date_obj = timezone.now().date()
        else:
            date_obj = timezone.now().date()

        return timezone.make_aware(
            dt.datetime.combine(date_obj, dt.time(9, 0))
        )
