"""Django implementation of the event repository."""

import datetime as dt
from typing import Optional

from django.utils import timezone

from core_logic.entities.event import (
    EventEntity,
    MarkEntity,
    ParticipationMarkData,
    StudentSummary,
    VariantSummary,
)
from core_logic.interfaces.event_repo import CreateEventParams, IEventRepository
from events.models import Event, EventParticipation, Mark


class DjangoEventRepository(IEventRepository):
    def get_by_id(self, event_id: str) -> Optional[EventEntity]:
        event = Event.objects.select_related('work', 'course').filter(
            pk=event_id
        ).first()
        if not event:
            return None

        return EventEntity(
            id=str(event.pk),
            name=event.name,
            work_id=str(event.work_id),
            work_name=event.work.name,
            course_id=str(event.course_id) if event.course_id else None,
        )

    def get_student_mark(
        self,
        event_id: str,
        student_id: str,
    ) -> Optional[MarkEntity]:
        mark = Mark.objects.filter(
            participation__event_id=event_id,
            participation__student_id=student_id,
        ).first()
        if not mark:
            return None

        return MarkEntity(
            student_id=str(student_id),
            event_id=str(event_id),
            score=mark.score,
        )

    def get_participation_marks(self, event_id: str):
        participations = EventParticipation.objects.filter(
            event_id=event_id
        ).select_related('student', 'variant').order_by(
            'student__last_name',
            'student__first_name',
        )

        marks = {
            mark.participation_id: mark
            for mark in Mark.objects.filter(
                participation_id__in=[p.pk for p in participations]
            )
        }

        result = []
        for participation in participations:
            student = participation.student
            variant = participation.variant
            mark = marks.get(participation.pk)
            result.append(
                ParticipationMarkData(
                    student=StudentSummary(
                        id=str(student.pk),
                        full_name=student.get_full_name(),
                    ),
                    variant=(
                        VariantSummary(
                            id=str(variant.pk),
                            number=variant.number,
                        )
                        if variant
                        else None
                    ),
                    score=mark.score if mark else None,
                    points=mark.points if mark else None,
                    max_points=mark.max_points if mark else None,
                    task_scores=mark.task_scores if mark else {},
                )
            )
        return result

    def create_event(self, params: CreateEventParams) -> str:
        planned_date = self._parse_planned_date(params.date)
        event = Event.objects.create(
            name=params.name,
            work_id=params.work_id,
            planned_date=planned_date,
            status='planned',
            course_id=params.course_id,
            description=params.description,
        )
        return str(event.pk)

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

    @staticmethod
    def _parse_planned_date(date_value: Optional[str]):
        if date_value:
            try:
                date_obj = dt.datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                date_obj = timezone.now().date()
        else:
            date_obj = timezone.now().date()

        return timezone.make_aware(
            dt.datetime.combine(date_obj, dt.time(9, 0))
        )
