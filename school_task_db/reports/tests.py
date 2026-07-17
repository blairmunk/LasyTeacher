from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Course, Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from tasks.models import Task
from works.models import Work


class ReportsViewsTests(TestCase):
    def test_heatmap_view_uses_clean_overview_data(self):
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        group = StudentGroup.objects.create(name='7А')
        group.students.add(student)
        Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )

        response = self.client.get(
            reverse('reports:heatmap'),
            {'group': group.pk, 'section': 'Кинематика'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'heatmap')
        self.assertEqual(response.context['selected_group'], group)
        self.assertEqual(response.context['selected_section'], 'Кинематика')
        self.assertEqual(response.context['sections'], ['Кинематика'])
        self.assertFalse(response.context['has_data'])

    def test_heatmap_view_uses_clean_topic_matrix_data(self):
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        group = StudentGroup.objects.create(name='7А')
        group.students.add(student)
        work = Work.objects.create(name='Контрольная')
        topic = Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )
        task = Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        event = Event.objects.create(
            name='КР',
            work=work,
            status='graded',
            planned_date=timezone.now(),
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
                str(task.pk): {'points': 8, 'max_points': 10},
            },
        )

        response = self.client.get(
            reverse('reports:heatmap'),
            {'group': group.pk, 'section': 'Кинематика'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['has_data'])
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['total_topics'], 1)
        self.assertEqual(response.context['grid_rows'][0]['avg'], 80)
        self.assertEqual(response.context['grid_col_averages'], [
            {'pct': 80, 'css': 'good'},
        ])

    def test_dashboard_view_uses_clean_report_data(self):
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

        response = self.client.get(reverse('reports:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'dashboard')
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['total_events'], 1)
        self.assertEqual(response.context['total_marks'], 1)
        self.assertEqual(response.context['class_stats'][0]['name'], '7А')
        self.assertEqual(list(response.context['recent_events']), [event])
        self.assertIn('score_chart_json', response.context)

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

    def test_work_analysis_view_uses_clean_report_data(self):
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
            score=5,
            points=10,
            max_points=10,
            task_scores={
                '550e8400-e29b-41d4-a716-446655440001': {
                    'points': 10,
                    'max_points': 10,
                },
            },
        )

        response = self.client.get(reverse('reports:work-analysis'))
        work_stat = response.context['works_analysis'][0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'work-analysis')
        self.assertEqual(work_stat['work'], work)
        self.assertEqual(work_stat['average_percentage'], 100)
        self.assertEqual(work_stat['difficulty_assessment'], 'Легкая')
        self.assertEqual(response.context['summary_stats']['total_works'], 1)

    def test_student_performance_view_uses_clean_report_data(self):
        now = timezone.now()
        work = Work.objects.create(name='Контрольная')
        student = Student.objects.create(last_name='Смирнов', first_name='Семён')
        group = StudentGroup.objects.create(name='9А')
        group.students.add(student)
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
            points=7,
            max_points=10,
            task_scores={
                '550e8400-e29b-41d4-a716-446655440001': {
                    'points': 7,
                    'max_points': 10,
                },
            },
        )

        response = self.client.get(
            reverse('reports:student-performance'),
            {'group': group.pk},
        )
        student_stat = response.context['students_stats'][0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'student-performance')
        self.assertEqual(response.context['selected_group'], group)
        self.assertEqual(student_stat['student'], student)
        self.assertEqual(student_stat['average_pct'], 70)
        self.assertEqual(student_stat['completion_rate'], 100)
        self.assertEqual(response.context['summary_stats']['total_students'], 1)
