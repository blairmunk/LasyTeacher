"""Django implementation of report repository."""

from datetime import timedelta

from django.db.models import Count

from core_logic.entities.report import EventsStatusReportData
from core_logic.interfaces.report_repo import IReportRepository
from curriculum.models import Course
from events.models import Event, EventParticipation


class DjangoReportRepository(IReportRepository):
    def get_events_status_report(self, year, current_date):
        events, participations, courses = self._get_event_scope(year)

        events_by_status = list(
            events.values('status').annotate(
                count=Count('id'),
            ).order_by('status'),
        )
        participation_stats = list(
            participations.values('status').annotate(
                count=Count('id'),
            ).order_by('status'),
        )

        return EventsStatusReportData(
            events_by_status=events_by_status,
            overdue_events=events.filter(
                status='planned',
                planned_date__lt=current_date - timedelta(days=1),
            ).select_related('work'),
            long_reviewing=events.filter(
                status='reviewing',
                actual_end__lt=current_date - timedelta(days=7),
            ).select_related('work'),
            completed_unchecked=events.filter(
                status='completed',
                actual_end__lt=current_date - timedelta(days=3),
            ).select_related('work'),
            participation_stats=participation_stats,
            all_events=events.select_related('work').order_by('-planned_date'),
            courses=courses.order_by('grade_level', 'name'),
        )

    def _get_event_scope(self, year):
        if year:
            date_range = (year.start_date, year.end_date)
            events = Event.objects.filter(planned_date__range=date_range)
            participations = EventParticipation.objects.filter(
                event__planned_date__range=date_range,
            )
            courses = Course.objects.filter(year=year, is_active=True)
        else:
            events = Event.objects.all()
            participations = EventParticipation.objects.all()
            courses = Course.objects.filter(is_active=True)

        return events, participations, courses
