from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from curriculum.models import Course, Topic
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_report_repo import DjangoReportRepository
from students.models import Student, StudentGroup
from works.models import Work


class DjangoReportRepositoryTests(TestCase):
    def test_get_heatmap_overview_returns_groups_students_and_sections(self):
        selected_student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        other_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        selected_group = StudentGroup.objects.create(name='7А')
        other_group = StudentGroup.objects.create(name='8Б')
        selected_group.students.add(selected_student)
        other_group.students.add(other_student)
        Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )
        Topic.objects.create(
            name='Степень',
            subject='Математика',
            section='Алгебра',
            grade_level=7,
        )
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )

        data = DjangoReportRepository().get_heatmap_overview(
            group_id=selected_group.pk,
        )

        self.assertEqual(list(data.groups), [selected_group, other_group])
        self.assertEqual(data.selected_group, selected_group)
        self.assertEqual(data.students, [selected_student])
        self.assertEqual(data.sections, ['Кинематика'])
        self.assertEqual(list(data.courses), [course])
        self.assertEqual(data.active_report, 'heatmap')

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

    def test_get_student_performance_report_returns_group_stats(self):
        now = timezone.now()
        work = Work.objects.create(name='Контрольная')
        selected_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        other_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )
        selected_group = StudentGroup.objects.create(name='7А')
        other_group = StudentGroup.objects.create(name='8Б')
        selected_group.students.add(selected_student)
        other_group.students.add(other_student)
        event = Event.objects.create(
            name='КР',
            work=work,
            status='graded',
            planned_date=now,
        )
        selected_participation = EventParticipation.objects.create(
            event=event,
            student=selected_student,
            status='graded',
        )
        EventParticipation.objects.create(
            event=event,
            student=other_student,
            status='assigned',
        )
        Mark.objects.create(
            participation=selected_participation,
            score=5,
            points=9,
            max_points=10,
            task_scores={
                '550e8400-e29b-41d4-a716-446655440001': {
                    'points': 9,
                    'max_points': 10,
                },
            },
        )

        data = DjangoReportRepository().get_student_performance_report(
            year=None,
            group_id=selected_group.pk,
        )
        stat = data.students_stats[0]

        self.assertEqual(data.selected_group, selected_group)
        self.assertEqual(data.groups.count(), 2)
        self.assertEqual(len(data.students_stats), 1)
        self.assertEqual(stat['student'], selected_student)
        self.assertEqual(stat['total_participations'], 1)
        self.assertEqual(stat['completed_participations'], 1)
        self.assertEqual(stat['completion_rate'], 100)
        self.assertEqual(stat['total_marks'], 1)
        self.assertEqual(stat['average_score'], 5)
        self.assertEqual(stat['average_pct'], 90)
        self.assertEqual(data.summary_stats['total_students'], 1)
        self.assertEqual(data.summary_stats['high_performers'], 1)
        self.assertEqual(data.summary_stats['need_attention'], 0)
        self.assertEqual(data.summary_stats['avg_completion_rate'], 100)
        self.assertEqual(data.summary_stats['avg_pct'], 90)
        self.assertEqual(data.active_report, 'student-performance')

    def test_get_reports_dashboard_returns_dashboard_data(self):
        now = timezone.now()
        work = Work.objects.create(name='Контрольная')
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        group = StudentGroup.objects.create(name='7А')
        group.students.add(student)
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )
        course.student_groups.add(group)
        event = Event.objects.create(
            name='КР',
            work=work,
            course=course,
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
            score=5,
            points=10,
            max_points=10,
            checked_at=now,
            task_scores={
                '550e8400-e29b-41d4-a716-446655440001': {
                    'points': 10,
                    'max_points': 10,
                },
            },
        )

        data = DjangoReportRepository().get_reports_dashboard(
            year=None,
            current_date=now,
        )
        class_stat = data.class_stats[0]

        self.assertEqual(data.total_students, 1)
        self.assertEqual(data.total_events, 1)
        self.assertEqual(data.total_works, 1)
        self.assertEqual(data.total_courses, 1)
        self.assertEqual(data.total_marks, 1)
        self.assertEqual(data.average_score, 5)
        self.assertEqual(data.marks_last_month, 1)
        self.assertEqual(data.score_counts, {5: 1})
        self.assertEqual(data.events_graded, 1)
        self.assertEqual(data.event_status_counts, {'graded': 1})
        self.assertEqual(data.monthly_values[-1], 1)
        self.assertEqual(class_stat['name'], '7А')
        self.assertEqual(class_stat['students_count'], 1)
        self.assertEqual(class_stat['completed_participations'], 1)
        self.assertEqual(class_stat['completion_rate'], 100)
        self.assertEqual(class_stat['heatmap_links'][0]['course_name'], 'Физика 7')
        self.assertEqual(list(data.recent_events), [event])
        self.assertEqual(data.box_data, {'Контрольная': [5]})
        self.assertEqual(data.active_report, 'dashboard')
