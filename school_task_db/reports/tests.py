import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup


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

    def test_heatmap_course_view_uses_clean_overview_data(self):
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

        response = self.client.get(
            reverse('reports:heatmap-course', args=[course.pk]),
            {'group': group.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'heatmap-course')
        self.assertEqual(response.context['active_course_pk'], course.pk)
        self.assertEqual(response.context['course'], course)
        self.assertEqual(response.context['selected_group'], group)
        self.assertFalse(response.context['has_data'])

    def test_heatmap_course_view_uses_clean_topic_matrix_data(self):
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
        work = Work.objects.create(name='Контрольная')
        CourseAssignment.objects.create(course=course, work=work)
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
        variant = Variant.objects.create(work=work, number=1)
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=10,
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
            reverse('reports:heatmap-course', args=[course.pk]),
            {'group': group.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['has_data'])
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['total_topics'], 1)
        self.assertEqual(response.context['grid_rows'][0]['avg'], 80)
        self.assertEqual(response.context['grid_col_averages'], [
            {'pct': 80, 'css': 'good'},
        ])
        timeline = json.loads(response.context['timeline_json'])
        self.assertEqual(timeline['data'][0]['y'], [80])
        self.assertEqual(timeline['data'][0]['text'], ['КР'])

    def test_heatmap_drilldown_view_uses_clean_subtopic_matrix_data(self):
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
        subtopic = SubTopic.objects.create(
            topic=topic,
            name='Средняя скорость',
            order=1,
        )
        task = Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=topic,
            subtopic=subtopic,
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
            reverse('reports:heatmap-drilldown', args=[topic.pk]),
            {'group': group.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'heatmap')
        self.assertEqual(response.context['topic'], topic)
        self.assertEqual(response.context['selected_group'], group)
        self.assertTrue(response.context['has_data'])
        self.assertEqual(response.context['grid_rows'][0]['avg'], 80)
        self.assertEqual(response.context['grid_col_averages'], [
            {'pct': 80, 'css': 'good'},
        ])

    def test_heatmap_student_view_uses_clean_detail_data(self):
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        work = Work.objects.create(name='Контрольная')
        topic = Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )
        subtopic = SubTopic.objects.create(
            topic=topic,
            name='Средняя скорость',
            order=1,
        )
        task = Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=topic,
            subtopic=subtopic,
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
            reverse('reports:heatmap-student', args=[topic.pk, student.pk]),
            {'subtopic': subtopic.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'heatmap')
        self.assertEqual(response.context['topic'], topic)
        self.assertEqual(response.context['student'].pk, str(student.pk))
        self.assertEqual(response.context['student'].full_name, student.get_full_name())
        self.assertEqual(response.context['selected_subtopic'], subtopic)
        self.assertEqual(response.context['details'][0]['task'], task)
        self.assertEqual(response.context['details'][0]['pct'], 80)
        self.assertEqual(response.context['subtopic_summary'][0]['pct'], 80)

    def test_heatmap_subtopic_view_uses_clean_detail_data(self):
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
        subtopic = SubTopic.objects.create(
            topic=topic,
            name='Средняя скорость',
            order=1,
        )
        task = Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=topic,
            subtopic=subtopic,
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
            reverse('reports:heatmap-subtopic', args=[subtopic.pk]),
            {'group': group.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'heatmap')
        self.assertEqual(response.context['subtopic'], subtopic)
        self.assertEqual(response.context['topic'], topic)
        self.assertEqual(response.context['selected_group'], group)
        self.assertEqual(response.context['group_param'], f'?group={group.pk}')
        self.assertEqual(response.context['overall_pct'], 80)
        self.assertEqual(response.context['students_with_data'], 1)
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['student_rows'][0]['pct'], 80)
        self.assertIn(f'group={group.pk}', response.context['student_rows'][0]['url'])
        self.assertEqual(response.context['task_rows'][0]['task'].pk, str(task.pk))
        self.assertEqual(response.context['task_rows'][0]['avg_pct'], 80)

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
        self.assertEqual(response.context['recent_events'][0].pk, str(event.pk))
        self.assertEqual(
            response.context['recent_events'][0].status_display,
            event.get_status_display(),
        )
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
        self.assertEqual(student_stat['student'].pk, str(student.pk))
        self.assertEqual(student_stat['student'].full_name, student.get_full_name())
        self.assertEqual(student_stat['average_pct'], 70)
        self.assertEqual(student_stat['completion_rate'], 100)
        self.assertEqual(response.context['summary_stats']['total_students'], 1)

    def test_journal_select_view_uses_clean_report_data(self):
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
        work = Work.objects.create(name='Контрольная')
        event = Event.objects.create(
            name='КР',
            work=work,
            course=course,
            status='planned',
            planned_date=timezone.now(),
        )
        EventParticipation.objects.create(
            event=event,
            student=student,
            status='assigned',
        )

        response = self.client.get(reverse('reports:journal-select'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'journal')
        self.assertEqual(list(response.context['courses']), [course])
        self.assertEqual(list(response.context['groups']), [group])
        link = response.context['journal_links'][0]
        self.assertEqual(link['course'].pk, str(course.pk))
        self.assertEqual(link['group'].pk, str(group.pk))
        self.assertEqual(link['group'].students_count, 1)
        self.assertEqual(link['event_count'], 1)

    def test_journal_view_uses_clean_report_data(self):
        now = timezone.now()
        work = Work.objects.create(name='Контрольная')
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )
        graded_student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        missing_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        group = StudentGroup.objects.create(name='7А')
        group.students.add(graded_student, missing_student)
        event = Event.objects.create(
            name='КР',
            work=work,
            course=course,
            status='graded',
            planned_date=now,
        )
        participation = EventParticipation.objects.create(
            event=event,
            student=graded_student,
            status='graded',
        )
        Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
            task_scores={
                '550e8400-e29b-41d4-a716-446655440001': {
                    'points': 8,
                    'max_points': 10,
                },
            },
        )

        response = self.client.get(
            reverse('reports:journal', args=[course.pk, group.pk]),
            {'debts': '1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'journal')
        self.assertEqual(response.context['course'], course)
        self.assertEqual(response.context['group'], group)
        self.assertEqual(list(response.context['events']), [event])
        self.assertTrue(response.context['show_debts_only'])
        self.assertEqual(response.context['all_rows_count'], 2)
        self.assertEqual(response.context['total_debts'], 1)
        self.assertEqual(response.context['students_with_debts'], 1)
        self.assertEqual(len(response.context['rows']), 1)
        self.assertEqual(response.context['rows'][0]['student'], missing_student)
        self.assertEqual(response.context['rows'][0]['cells'][0]['status'], 'missing')
        self.assertEqual(response.context['event_stats'][0]['graded'], 1)
        self.assertEqual(response.context['event_stats'][0]['missing'], 1)

    def test_db_health_view_uses_clean_report_data(self):
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
            is_verified=False,
            grade=None,
        )
        empty_group = AnalogGroup.objects.create(name='Пустая группа')
        fragile_group = AnalogGroup.objects.create(name='Хрупкая группа')
        TaskGroup.objects.create(task=task, group=fragile_group)
        work_no_spec = Work.objects.create(name='Без спецификации')
        spec_work = Work.objects.create(name='Со спецификацией')
        WorkAnalogGroup.objects.create(
            work=spec_work,
            analog_group=fragile_group,
            count=2,
        )
        Variant.objects.create(work=None, number=1)

        response = self.client.get(reverse('reports:db-health'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_report'], 'db-health')
        self.assertEqual(response.context['stats']['total_tasks'], 1)
        self.assertEqual(response.context['stats']['total_groups'], 2)
        self.assertEqual(response.context['orphan_variants']['count'], 1)
        self.assertEqual(response.context['empty_groups']['items'][0], empty_group)
        self.assertEqual(response.context['fragile_groups']['items'][0], fragile_group)
        self.assertEqual(response.context['coverage_issues']['items'][0]['work'], spec_work)
        self.assertEqual(response.context['works_no_spec']['items'][0], work_no_spec)
        self.assertEqual(response.context['unverified_tasks']['pct'], 100.0)
        self.assertEqual(response.context['health']['issues'], 7)
        self.assertEqual(response.context['health']['label'], 'Есть замечания')
