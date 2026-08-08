"""Pure calculations for the events status report."""

from collections import Counter
from datetime import timedelta

from core_logic.entities.report_summary import (
    EventsStatusReportData,
    EventsStatusSource,
)


class EventsStatusService:
    def build(
        self,
        source: EventsStatusSource,
        current_date,
    ) -> EventsStatusReportData:
        event_counts = Counter(event.status for event in source.events)
        participation_counts = Counter(source.participation_statuses)
        return EventsStatusReportData(
            events_by_status=[
                {'status': status, 'count': event_counts[status]}
                for status in sorted(event_counts)
            ],
            overdue_events=[
                event
                for event in source.events
                if event.status == 'planned'
                and event.planned_date < current_date - timedelta(days=1)
            ],
            long_reviewing=[
                event
                for event in source.events
                if event.status == 'reviewing'
                and event.actual_end is not None
                and event.actual_end < current_date - timedelta(days=7)
            ],
            completed_unchecked=[
                event
                for event in source.events
                if event.status == 'completed'
                and event.actual_end is not None
                and event.actual_end < current_date - timedelta(days=3)
            ],
            participation_stats=[
                {'status': status, 'count': participation_counts[status]}
                for status in sorted(participation_counts)
            ],
            all_events=source.events,
            courses=source.courses,
        )
