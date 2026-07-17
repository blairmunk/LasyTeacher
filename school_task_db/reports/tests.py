from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event, EventParticipation
from students.models import Student
from works.models import Work


class ReportsViewsTests(TestCase):
    def test_events_status_view_uses_clean_report_data(self):
        now = timezone.now()
        work = Work.objects.create(name='Контрольная')
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        planned = Event.objects.create(
            name='Просроченная',
            work=work,
            status='planned',
            planned_date=now - timedelta(days=2),
        )
        EventParticipation.objects.create(
            event=planned,
            student=student,
            status='assigned',
        )

        response = self.client.get(reverse('reports:events-status'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'events-status')
        self.assertEqual(response.context['events_by_status'], [
            {'status': 'planned', 'count': 1},
        ])
        self.assertEqual(list(response.context['overdue_events']), [planned])
        self.assertEqual(response.context['participation_stats'], [
            {'status': 'assigned', 'count': 1},
        ])
