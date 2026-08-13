"""Django repository for event write operations."""

import datetime as dt
from typing import Optional

from django.utils import timezone

from core_logic.entities.event_commands import CreateEventParams
from core_logic.interfaces.event_write_repo import IEventWriteRepository
from events.models import Event


class DjangoEventWriteRepository(IEventWriteRepository):
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

    def set_event_status(self, event_id: str, status: str) -> None:
        Event.objects.filter(pk=event_id).update(status=status)

    @staticmethod
    def _parse_planned_date(
        date_value: Optional[dt.date | dt.datetime],
    ) -> dt.datetime:
        if isinstance(date_value, dt.datetime):
            if timezone.is_naive(date_value):
                return timezone.make_aware(date_value)
            return date_value

        date_obj = date_value or timezone.now().date()

        return timezone.make_aware(
            dt.datetime.combine(date_obj, dt.time(9, 0))
        )
