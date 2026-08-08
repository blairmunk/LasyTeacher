"""Django read adapter for the events status report."""

from core_logic.entities.report_summary import EventsStatusSource
from core_logic.interfaces.events_status_repo import IEventsStatusRepository
from infrastructure.repositories.django_report_summary_support import (
    event_scope,
    event_summary_queryset,
    report_course_ref,
    report_event_ref,
)


class DjangoEventsStatusRepository(IEventsStatusRepository):
    def get_events_status_source(self, year):
        events, participations, courses = event_scope(year)
        return EventsStatusSource(
            events=[
                report_event_ref(event)
                for event in event_summary_queryset(events).order_by(
                    '-planned_date',
                )
            ],
            participation_statuses=list(
                participations.values_list('status', flat=True)
            ),
            courses=[
                report_course_ref(course)
                for course in courses.order_by('grade_level', 'name')
            ],
        )
