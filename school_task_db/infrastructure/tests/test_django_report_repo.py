from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_report_repo import DjangoReportRepository
from students.models import Student
from works.models import Work


class DjangoReportRepositoryTests(TestCase):
    def test_get_events_status_report_returns_status_context(self):
        now = timezone.now()
        work = Work.objects.create(name='Контрольная')
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        planned = Event.objects.create(
            name='Просроченная',
            work=work,
            status='planned',
            planned_date=now - timedelta(days=2),
        )
        reviewing = Event.objects.create(
            name='Долго проверяется',
            work=work,
            status='reviewing',
            planned_date=now - timedelta(days=10),
            actual_end=now - timedelta(days=8),
        )
        completed = Event.objects.create(
            name='Не проверена',
            work=work,
            status='completed',
            planned_date=now - timedelta(days=5),
            actual_end=now - timedelta(days=4),
        )
        EventParticipation.objects.create(
            event=planned,
            student=student,
            status='assigned',
        )
        EventParticipation.objects.create(
            event=reviewing,
            student=student,
            status='graded',
        )

        data = DjangoReportRepository().get_events_status_report(
            year=None,
            current_date=now,
        )

        status_counts = {
            item['status']: item['count']
            for item in data.events_by_status
        }
        participation_counts = {
            item['status']: item['count']
            for item in data.participation_stats
        }

        self.assertEqual(status_counts['planned'], 1)
        self.assertEqual(status_counts['reviewing'], 1)
        self.assertEqual(status_counts['completed'], 1)
        self.assertEqual(participation_counts['assigned'], 1)
        self.assertEqual(participation_counts['graded'], 1)
        self.assertEqual(list(data.overdue_events), [planned])
        self.assertEqual(list(data.long_reviewing), [reviewing])
        self.assertEqual(list(data.completed_unchecked), [completed])
        self.assertEqual(list(data.all_events), [planned, completed, reviewing])
        self.assertEqual(data.active_report, 'events-status')

    def test_get_work_analysis_report_returns_work_stats(self):
        now = timezone.now()
        work = Work.objects.create(name='Контрольная')
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        event = Event.objects.create(
            name='КР',
            work=work,
            status='graded',
            planned_date=now,
        )
        participation = EventParticipation.objects.create(
            event=event,
            student=student,
            status='graded',
        )
        Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
            task_scores={
                '550e8400-e29b-41d4-a716-446655440001': {
                    'points': 3,
                    'max_points': 5,
                },
                '550e8400-e29b-41d4-a716-446655440002': {
                    'points': 5,
                    'max_points': 5,
                },
            },
        )

        data = DjangoReportRepository().get_work_analysis_report(year=None)
        work_stat = data.works_analysis[0]

        self.assertEqual(work_stat['work'], work)
        self.assertEqual(work_stat['events_count'], 1)
        self.assertEqual(work_stat['total_marks'], 1)
        self.assertEqual(work_stat['average_score'], 4)
        self.assertEqual(work_stat['average_percentage'], 80)
        self.assertEqual(work_stat['difficulty_assessment'], 'Средняя')
        self.assertEqual(work_stat['score_distribution'], [
            {'score': 4, 'count': 1},
        ])
        self.assertEqual(data.summary_stats['total_works'], 1)
        self.assertEqual(data.summary_stats['total_marks'], 1)
        self.assertEqual(data.summary_stats['avg_score'], 4)
        self.assertEqual(data.active_report, 'work-analysis')
