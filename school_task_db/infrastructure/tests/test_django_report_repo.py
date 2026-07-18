from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_report_repo import DjangoReportRepository
from students.models import Student, StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup


class DjangoReportRepositoryTests(TestCase):
    def test_get_heatmap_drilldown_overview_returns_topic_scope(self):
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
        topic = Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )

        data = DjangoReportRepository().get_heatmap_drilldown_overview(
            topic_id=topic.pk,
            group_id=selected_group.pk,
        )

        self.assertEqual(data.topic, topic)
        self.assertEqual(list(data.groups), [selected_group, other_group])
        self.assertEqual(data.selected_group, selected_group)
        self.assertEqual(data.students, [selected_student])
        self.assertEqual(list(data.courses), [course])
        self.assertEqual(data.active_report, 'heatmap')

    def test_get_heatmap_subtopic_matrix_returns_subtopic_scores(self):
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
        other_subtopic = SubTopic.objects.create(
            topic=topic,
            name='Путь',
            order=2,
        )
        task = Task.objects.create(
            text='Задача 1',
            answer='Ответ',
            topic=topic,
            subtopic=subtopic,
            task_type='computational',
            difficulty=2,
        )
        other_task = Task.objects.create(
            text='Задача 2',
            answer='Ответ',
            topic=topic,
            subtopic=other_subtopic,
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

        data = DjangoReportRepository().get_heatmap_subtopic_matrix(
            student_ids=[student.pk],
            topic_id=topic.pk,
        )

        self.assertEqual(data.columns, [subtopic])
        self.assertEqual(len(data.rows), 1)
        self.assertEqual(data.rows[0]['student'], student)
        self.assertEqual(data.rows[0]['avg'], 80)
        self.assertEqual(data.rows[0]['cells'][0]['pct'], 80)
        self.assertEqual(data.rows[0]['cells'][0]['subtopic'], subtopic)
        self.assertEqual(data.col_averages, [{'pct': 80, 'css': 'good'}])

    def test_get_heatmap_subtopic_detail_returns_student_and_task_rows(self):
        selected_student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        empty_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        other_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )
        selected_group = StudentGroup.objects.create(name='7А')
        other_group = StudentGroup.objects.create(name='8Б')
        selected_group.students.add(selected_student, empty_student)
        other_group.students.add(other_student)
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
        other_subtopic = SubTopic.objects.create(
            topic=topic,
            name='Путь',
            order=2,
        )
        task = Task.objects.create(
            text='Задача 1',
            answer='Ответ',
            topic=topic,
            subtopic=subtopic,
            task_type='computational',
            difficulty=2,
        )
        other_task = Task.objects.create(
            text='Задача 2',
            answer='Ответ',
            topic=topic,
            subtopic=other_subtopic,
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
            student=selected_student,
            status='graded',
        )
        Mark.objects.create(
            participation=participation,
            score=4,
            points=10,
            max_points=20,
            task_scores={
                str(task.pk): {'points': 8, 'max_points': 10},
                str(other_task.pk): {'points': 2, 'max_points': 10},
            },
        )

        data = DjangoReportRepository().get_heatmap_subtopic_detail(
            subtopic_id=subtopic.pk,
            group_id=selected_group.pk,
        )

        self.assertEqual(data.subtopic, subtopic)
        self.assertEqual(data.topic, topic)
        self.assertEqual(list(data.groups), [selected_group, other_group])
        self.assertEqual(data.selected_group, selected_group)
        self.assertEqual(data.total_students, 2)
        self.assertEqual(data.students_with_data, 1)
        self.assertEqual(data.overall_pct, 80)
        self.assertEqual(data.overall_css, 'good')
        self.assertEqual(data.student_rows[0]['student'], selected_student)
        self.assertEqual(data.student_rows[0]['points'], 8)
        self.assertEqual(data.student_rows[0]['max_points'], 10)
        self.assertEqual(data.student_rows[0]['pct'], 80)
        self.assertEqual(data.student_rows[0]['events'], ['КР'])
        self.assertEqual(data.student_rows[1]['student'], empty_student)
        self.assertIsNone(data.student_rows[1]['pct'])
        self.assertEqual(data.task_rows[0]['task'], task)
        self.assertEqual(data.task_rows[0]['avg_pct'], 80)
        self.assertEqual(data.task_rows[0]['students_count'], 1)
        self.assertEqual(data.active_report, 'heatmap')

    def test_get_heatmap_student_detail_returns_details_and_summary(self):
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
        other_subtopic = SubTopic.objects.create(
            topic=topic,
            name='Путь',
            order=2,
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

        data = DjangoReportRepository().get_heatmap_student_detail(
            topic_id=topic.pk,
            student_id=student.pk,
            subtopic_id=subtopic.pk,
        )

        self.assertEqual(data.topic, topic)
        self.assertEqual(data.student, student)
        self.assertEqual(data.selected_subtopic, subtopic)
        self.assertEqual(len(data.details), 1)
        self.assertEqual(data.details[0]['task'], task)
        self.assertEqual(data.details[0]['pct'], 80)
        self.assertEqual(data.subtopic_summary[0]['subtopic'], subtopic)
        self.assertEqual(data.subtopic_summary[0]['pct'], 80)
        self.assertTrue(data.subtopic_summary[0]['is_selected'])
        self.assertEqual(data.subtopic_summary[1]['subtopic'], other_subtopic)
        self.assertIsNone(data.subtopic_summary[1]['pct'])
        self.assertEqual(data.active_report, 'heatmap')

    def test_get_heatmap_course_overview_returns_course_scope(self):
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
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )
        course.student_groups.add(selected_group)
        work = Work.objects.create(name='Контрольная')
        CourseAssignment.objects.create(course=course, work=work)

        data = DjangoReportRepository().get_heatmap_course_overview(
            course_id=course.pk,
            group_id=selected_group.pk,
        )

        self.assertEqual(data.course, course)
        self.assertEqual(list(data.groups), [selected_group])
        self.assertEqual(data.selected_group, selected_group)
        self.assertEqual(data.students, [selected_student])
        self.assertEqual(data.course_works, [work])
        self.assertEqual(list(data.courses), [course])
        self.assertEqual(data.active_report, 'heatmap-course')
        self.assertEqual(data.active_course_pk, course.pk)

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

    def test_get_heatmap_topic_matrix_returns_topic_scores(self):
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        work = Work.objects.create(name='Контрольная')
        topic = Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )
        other_topic = Topic.objects.create(
            name='Сила',
            subject='Физика',
            section='Динамика',
            grade_level=7,
        )
        task = Task.objects.create(
            text='Задача 1',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        other_task = Task.objects.create(
            text='Задача 2',
            answer='Ответ',
            topic=other_topic,
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
                str(other_task.pk): {'points': 2, 'max_points': 10},
            },
        )

        data = DjangoReportRepository().get_heatmap_topic_matrix(
            student_ids=[student.pk],
            section_filter='Кинематика',
        )

        self.assertEqual(data.columns, [topic])
        self.assertEqual(len(data.rows), 1)
        self.assertEqual(data.rows[0]['student'], student)
        self.assertEqual(data.rows[0]['avg'], 80)
        self.assertEqual(data.rows[0]['avg_css'], 'good')
        self.assertEqual(data.rows[0]['cells'][0]['pct'], 80)
        self.assertEqual(data.rows[0]['cells'][0]['css'], 'good')
        self.assertEqual(data.col_averages, [{'pct': 80, 'css': 'good'}])

    def test_get_heatmap_course_topic_matrix_returns_course_scores(self):
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        course_work = Work.objects.create(name='Работа курса')
        other_work = Work.objects.create(name='Другая работа')
        topic = Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )
        other_topic = Topic.objects.create(
            name='Сила',
            subject='Физика',
            section='Динамика',
            grade_level=7,
        )
        task = Task.objects.create(
            text='Задача курса',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        other_task = Task.objects.create(
            text='Задача не из курса',
            answer='Ответ',
            topic=other_topic,
            task_type='computational',
            difficulty=2,
        )
        variant = Variant.objects.create(work=course_work, number=1)
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=10,
        )
        course_event = Event.objects.create(
            name='КР',
            work=course_work,
            status='graded',
            planned_date=timezone.now(),
        )
        other_event = Event.objects.create(
            name='Другая КР',
            work=other_work,
            status='graded',
            planned_date=timezone.now(),
        )
        participation = EventParticipation.objects.create(
            event=course_event,
            student=student,
            status='graded',
        )
        other_participation = EventParticipation.objects.create(
            event=other_event,
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
                str(other_task.pk): {'points': 1, 'max_points': 10},
            },
        )
        Mark.objects.create(
            participation=other_participation,
            score=5,
            points=10,
            max_points=10,
            task_scores={
                str(other_task.pk): {'points': 10, 'max_points': 10},
            },
        )

        data = DjangoReportRepository().get_heatmap_course_topic_matrix(
            student_ids=[student.pk],
            work_ids=[course_work.pk],
        )

        self.assertEqual(data.columns, [topic])
        self.assertEqual(len(data.rows), 1)
        self.assertEqual(data.rows[0]['student'], student)
        self.assertEqual(data.rows[0]['avg'], 80)
        self.assertEqual(data.rows[0]['cells'][0]['pct'], 80)
        self.assertEqual(data.col_averages, [{'pct': 80, 'css': 'good'}])

    def test_get_heatmap_course_timeline_returns_event_averages(self):
        now = timezone.now()
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        work = Work.objects.create(name='Работа курса')
        event = Event.objects.create(
            name='КР',
            work=work,
            status='graded',
            planned_date=now,
        )
        planned_event = Event.objects.create(
            name='План',
            work=work,
            status='planned',
            planned_date=now + timedelta(days=7),
        )
        participation = EventParticipation.objects.create(
            event=event,
            student=student,
            status='graded',
        )
        EventParticipation.objects.create(
            event=planned_event,
            student=student,
            status='assigned',
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

        data = DjangoReportRepository().get_heatmap_course_timeline(
            student_ids=[student.pk],
            work_ids=[work.pk],
        )

        self.assertEqual(data.dates, [now.strftime('%Y-%m-%d')])
        self.assertEqual(data.averages, [80])
        self.assertEqual(data.labels, ['КР'])

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
        self.assertEqual(stat['student'].pk, str(selected_student.pk))
        self.assertEqual(stat['student'].full_name, selected_student.get_full_name())
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

    def test_get_journal_select_returns_course_group_links(self):
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

        data = DjangoReportRepository().get_journal_select(year=None)

        self.assertEqual(list(data.groups), [group])
        self.assertEqual(list(data.courses), [course])
        self.assertEqual(data.journal_links, [{
            'course': course,
            'group': group,
            'event_count': 1,
        }])
        self.assertEqual(data.active_report, 'journal')

    def test_get_journal_returns_rows_stats_and_debt_filter(self):
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

        data = DjangoReportRepository().get_journal(
            course_id=course.pk,
            group_id=group.pk,
            year=None,
            show_debts_only=True,
        )

        self.assertEqual(data.course, course)
        self.assertEqual(data.group, group)
        self.assertEqual(list(data.events), [event])
        self.assertEqual(data.all_rows_count, 2)
        self.assertTrue(data.show_debts_only)
        self.assertEqual(data.total_debts, 1)
        self.assertEqual(data.students_with_debts, 1)
        self.assertEqual(len(data.rows), 1)
        self.assertEqual(data.rows[0]['student'], missing_student)
        self.assertEqual(data.rows[0]['cells'][0]['status'], 'missing')
        self.assertEqual(data.rows[0]['cells'][0]['css_class'], 'journal-missing')
        self.assertEqual(data.event_stats, [{
            'event': event,
            'graded': 1,
            'absent': 0,
            'missing': 1,
            'total': 2,
        }])
        self.assertEqual(data.active_report, 'journal')

    def test_get_task_db_health_returns_database_health_data(self):
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
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )

        data = DjangoReportRepository().get_task_db_health()

        self.assertEqual(data.stats, {
            'total_tasks': 1,
            'total_groups': 2,
            'total_works': 2,
            'total_variants': 1,
        })
        self.assertEqual(data.orphan_variants['count'], 1)
        self.assertEqual(data.empty_groups['count'], 1)
        self.assertEqual(list(data.empty_groups['items']), [empty_group])
        self.assertEqual(data.fragile_groups['count'], 1)
        self.assertEqual(list(data.fragile_groups['items']), [fragile_group])
        self.assertEqual(data.coverage_issues['items'][0]['work'], spec_work)
        self.assertEqual(data.coverage_issues['items'][0]['group'], fragile_group)
        self.assertEqual(data.coverage_issues['items'][0]['needed'], 2)
        self.assertEqual(data.coverage_issues['items'][0]['available'], 1)
        self.assertEqual(data.ungrouped_tasks, {'count': 0, 'pct': 0.0})
        self.assertEqual(data.works_no_variants['count'], 2)
        self.assertEqual(list(data.works_no_spec['items']), [work_no_spec])
        self.assertEqual(data.difficulty_dist, [{
            'difficulty': 2,
            'count': 1,
            'pct': 100.0,
        }])
        self.assertEqual(data.type_dist[0]['task_type'], 'computational')
        self.assertEqual(data.type_dist[0]['pct'], 100.0)
        self.assertEqual(data.unverified_tasks, {'count': 1, 'pct': 100.0})
        self.assertEqual(data.no_source_tasks, {'count': 1, 'pct': 100.0})
        self.assertEqual(data.no_grade_tasks, {'count': 1, 'pct': 100.0})
        self.assertEqual(data.health['issues'], 7)
        self.assertEqual(data.health['label'], 'Есть замечания')
        self.assertEqual(list(data.courses), [course])
        self.assertEqual(data.active_report, 'db-health')

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
