from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_report_repo import DjangoReportRepository
from infrastructure.tests.variant_task_factory import (
    capture_attempt_snapshot,
    create_variant_task,
)
from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    GetHeatmapCourseTopicMatrixUseCase,
    HeatmapCourseTopicMatrixRequest,
)
from core_logic.use_cases.get_heatmap_topic_matrix import (
    GetHeatmapTopicMatrixUseCase,
    HeatmapTopicMatrixRequest,
)
from core_logic.use_cases.get_heatmap_subtopic_matrix import (
    GetHeatmapSubtopicMatrixUseCase,
    HeatmapSubtopicMatrixRequest,
)
from core_logic.use_cases.get_heatmap_subtopic_detail import (
    GetHeatmapSubtopicDetailUseCase,
    HeatmapSubtopicDetailRequest,
)
from core_logic.use_cases.get_heatmap_student_detail import (
    GetHeatmapStudentDetailUseCase,
    HeatmapStudentDetailRequest,
)
from core_logic.use_cases.get_work_analysis_report import (
    GetWorkAnalysisReportUseCase,
    WorkAnalysisReportRequest,
)
from core_logic.use_cases.get_student_performance_report import (
    GetStudentPerformanceReportUseCase,
    StudentPerformanceReportRequest,
)
from core_logic.use_cases.get_events_status_report import (
    EventsStatusReportRequest,
    GetEventsStatusReportUseCase,
)
from core_logic.use_cases.get_reports_dashboard import (
    GetReportsDashboardUseCase,
    ReportsDashboardRequest,
)
from students.models import Student, StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, Work, WorkAnalogGroup


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

        self.assertEqual(data.topic.pk, str(topic.pk))
        self.assertEqual(
            [group.pk for group in data.groups],
            [str(selected_group.pk), str(other_group.pk)],
        )
        self.assertEqual(data.selected_group.pk, str(selected_group.pk))
        self.assertEqual(data.students[0].pk, str(selected_student.pk))
        self.assertEqual(data.courses[0].pk, str(course.pk))
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
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
            task_scores={
                'variant-task-1': {
                    'task_id': str(task.pk),
                    'points': 8,
                    'max_points': 10,
                },
            },
        )
        capture_attempt_snapshot(mark)

        data = GetHeatmapSubtopicMatrixUseCase(
            DjangoReportRepository(),
        ).execute(
            HeatmapSubtopicMatrixRequest(
                student_ids=[student.pk],
                topic_id=topic.pk,
            ),
        )

        self.assertEqual(data.columns[0].pk, str(subtopic.pk))
        self.assertEqual(data.columns[0].name, subtopic.name)
        self.assertEqual(len(data.rows), 1)
        self.assertEqual(data.rows[0]['student'].pk, str(student.pk))
        self.assertEqual(
            data.rows[0]['student'].short_name,
            student.get_short_name(),
        )
        self.assertEqual(data.rows[0]['avg'], 80)
        self.assertEqual(data.rows[0]['cells'][0]['pct'], 80)
        self.assertEqual(
            data.rows[0]['cells'][0]['subtopic'].pk,
            str(subtopic.pk),
        )
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
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=10,
            max_points=20,
            task_scores={
                'variant-task-1': {
                    'task_id': str(task.pk),
                    'points': 8,
                    'max_points': 10,
                },
                str(other_task.pk): {'points': 2, 'max_points': 10},
            },
        )
        capture_attempt_snapshot(mark)
        task.text = 'Изменённое задание банка'
        task.save(update_fields=['text'])
        event.name = 'Изменённое событие'
        event.save(update_fields=['name'])

        data = GetHeatmapSubtopicDetailUseCase(
            DjangoReportRepository(),
        ).execute(
            HeatmapSubtopicDetailRequest(
                subtopic_id=subtopic.pk,
                group_id=selected_group.pk,
            ),
        )

        self.assertEqual(data.subtopic.pk, str(subtopic.pk))
        self.assertEqual(data.topic.pk, str(topic.pk))
        self.assertEqual(
            [group.pk for group in data.groups],
            [str(selected_group.pk), str(other_group.pk)],
        )
        self.assertEqual(data.selected_group.pk, str(selected_group.pk))
        self.assertEqual(data.total_students, 2)
        self.assertEqual(data.students_with_data, 1)
        self.assertEqual(data.overall_pct, 80)
        self.assertEqual(data.overall_css, 'good')
        self.assertEqual(data.student_rows[0]['student'].pk, str(selected_student.pk))
        self.assertEqual(
            data.student_rows[0]['student'].short_name,
            selected_student.get_short_name(),
        )
        self.assertEqual(data.student_rows[0]['points'], 8)
        self.assertEqual(data.student_rows[0]['max_points'], 10)
        self.assertEqual(data.student_rows[0]['pct'], 80)
        self.assertEqual(data.student_rows[0]['events'], ['КР'])
        self.assertEqual(data.student_rows[1]['student'].pk, str(empty_student.pk))
        self.assertIsNone(data.student_rows[1]['pct'])
        self.assertEqual(data.task_rows[0]['task'].pk, str(task.pk))
        self.assertEqual(data.task_rows[0]['task'].text, 'Задача 1')
        self.assertEqual(
            data.task_rows[0]['task'].difficulty_display,
            task.get_difficulty_display(),
        )
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
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
            task_scores={
                'variant-task-1': {
                    'task_id': str(task.pk),
                    'points': 8,
                    'max_points': 10,
                },
            },
        )
        capture_attempt_snapshot(mark)

        data = GetHeatmapStudentDetailUseCase(
            DjangoReportRepository(),
        ).execute(
            HeatmapStudentDetailRequest(
                topic_id=topic.pk,
                student_id=student.pk,
                subtopic_id=subtopic.pk,
            ),
        )

        self.assertEqual(data.topic.pk, str(topic.pk))
        self.assertEqual(data.student.pk, str(student.pk))
        self.assertEqual(data.student.full_name, student.get_full_name())
        self.assertEqual(data.selected_subtopic.pk, str(subtopic.pk))
        self.assertEqual(len(data.details), 1)
        self.assertEqual(data.details[0]['task'].pk, str(task.pk))
        self.assertEqual(data.details[0]['pct'], 80)
        self.assertEqual(
            data.subtopic_summary[0]['subtopic'].pk,
            str(subtopic.pk),
        )
        self.assertEqual(data.subtopic_summary[0]['pct'], 80)
        self.assertTrue(data.subtopic_summary[0]['is_selected'])
        self.assertEqual(
            data.subtopic_summary[1]['subtopic'].pk,
            str(other_subtopic.pk),
        )
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

        self.assertEqual(data.course.pk, str(course.pk))
        self.assertEqual(data.groups[0].pk, str(selected_group.pk))
        self.assertEqual(data.selected_group.pk, str(selected_group.pk))
        self.assertEqual(data.students[0].pk, str(selected_student.pk))
        self.assertEqual(data.course_works[0].pk, str(work.pk))
        self.assertEqual(data.courses[0].pk, str(course.pk))
        self.assertEqual(data.active_report, 'heatmap-course')
        self.assertEqual(data.active_course_pk, str(course.pk))

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

        self.assertEqual(
            [group.pk for group in data.groups],
            [str(selected_group.pk), str(other_group.pk)],
        )
        self.assertEqual(data.selected_group.pk, str(selected_group.pk))
        self.assertEqual(data.students[0].pk, str(selected_student.pk))
        self.assertEqual(data.sections, ['Кинематика'])
        self.assertEqual(data.courses[0].pk, str(course.pk))
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
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
            task_scores={
                'variant-task-1': {
                    'task_id': str(task.pk),
                    'points': 8,
                    'max_points': 10,
                },
                str(other_task.pk): {'points': 2, 'max_points': 10},
            },
        )
        capture_attempt_snapshot(mark)

        data = GetHeatmapTopicMatrixUseCase(
            DjangoReportRepository(),
        ).execute(
            HeatmapTopicMatrixRequest(
                student_ids=[student.pk],
                section_filter='Кинематика',
            ),
        )

        self.assertEqual(data.columns[0].pk, str(topic.pk))
        self.assertEqual(data.columns[0].name, topic.name)
        self.assertEqual(len(data.rows), 1)
        self.assertEqual(data.rows[0]['student'].pk, str(student.pk))
        self.assertEqual(
            data.rows[0]['student'].short_name,
            student.get_short_name(),
        )
        self.assertEqual(data.rows[0]['avg'], 80)
        self.assertEqual(data.rows[0]['avg_css'], 'good')
        self.assertEqual(data.rows[0]['cells'][0]['pct'], 80)
        self.assertEqual(data.rows[0]['cells'][0]['css'], 'good')
        self.assertEqual(data.col_averages, [{'pct': 80, 'css': 'good'}])

    def test_heatmap_reads_captured_attempt_instead_of_live_mark(self):
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        work = Work.objects.create(name='Контрольная')
        topic = Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )
        task = Task.objects.create(
            text='Повторяющаяся задача',
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
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=3,
            max_points=4,
            task_scores={
                str(task.pk): {'points': 3, 'max_points': 4},
            },
        )
        capture_attempt_snapshot(mark)
        mark.task_scores = {
            str(task.pk): {'points': 0, 'max_points': 100},
        }
        mark.save(update_fields=['task_scores'])

        data = GetHeatmapTopicMatrixUseCase(
            DjangoReportRepository(),
        ).execute(
            HeatmapTopicMatrixRequest(
                student_ids=[student.pk],
                section_filter='Кинематика',
            ),
        )

        self.assertEqual(data.rows[0]['cells'][0]['points'], 3)
        self.assertEqual(data.rows[0]['cells'][0]['max_points'], 4)
        self.assertEqual(data.rows[0]['cells'][0]['pct'], 75)

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
        create_variant_task(
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
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
            task_scores={
                'variant-task-1': {
                    'task_id': str(task.pk),
                    'points': 8,
                    'max_points': 10,
                },
            },
        )
        other_mark = Mark.objects.create(
            participation=other_participation,
            score=5,
            points=10,
            max_points=10,
            task_scores={
                str(other_task.pk): {'points': 10, 'max_points': 10},
            },
        )
        capture_attempt_snapshot(mark)
        capture_attempt_snapshot(other_mark)

        data = GetHeatmapCourseTopicMatrixUseCase(
            DjangoReportRepository(),
        ).execute(
            HeatmapCourseTopicMatrixRequest(
                student_ids=[student.pk],
                work_ids=[course_work.pk],
            ),
        )

        self.assertEqual(data.columns[0].pk, str(topic.pk))
        self.assertEqual(data.columns[0].name, topic.name)
        self.assertEqual(len(data.rows), 1)
        self.assertEqual(data.rows[0]['student'].pk, str(student.pk))
        self.assertEqual(
            data.rows[0]['student'].short_name,
            student.get_short_name(),
        )
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
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
            task_scores={
                '550e8400-e29b-41d4-a716-446655440001': {
                    'points': 0,
                    'max_points': 100,
                },
            },
        )
        capture_attempt_snapshot(mark)
        mark.points = 1
        mark.max_points = 100
        mark.save(update_fields=['points', 'max_points'])

        data = DjangoReportRepository().get_heatmap_course_timeline_source(
            student_ids=[student.pk],
            work_ids=[work.pk],
        )

        self.assertEqual(data.events[0].pk, str(event.pk))
        self.assertEqual(data.events[0].planned_date, now)
        self.assertEqual(data.events[0].name, 'КР')
        self.assertEqual(data.marks[0].event_id, str(event.pk))
        self.assertEqual(data.marks[0].points, 8)
        self.assertEqual(data.marks[0].max_points, 10)

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

        data = GetEventsStatusReportUseCase(
            DjangoReportRepository(),
        ).execute(
            EventsStatusReportRequest(
                year=None,
                current_date=now,
            ),
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
        self.assertEqual(data.overdue_events[0].pk, str(planned.pk))
        self.assertEqual(data.overdue_events[0].name, 'Просроченная')
        self.assertEqual(data.overdue_events[0].work.name, 'Контрольная')
        self.assertEqual(
            data.overdue_events[0].work.work_type_display,
            work.get_work_type_display(),
        )
        self.assertEqual(data.overdue_events[0].participants_count, 1)
        self.assertEqual(data.overdue_events[0].graded_count, 0)
        self.assertEqual(data.overdue_events[0].progress_percentage, 0)
        self.assertEqual(data.long_reviewing[0].pk, str(reviewing.pk))
        self.assertEqual(data.long_reviewing[0].participants_count, 1)
        self.assertEqual(data.long_reviewing[0].graded_count, 1)
        self.assertEqual(data.long_reviewing[0].progress_percentage, 100)
        self.assertEqual(data.completed_unchecked[0].pk, str(completed.pk))
        self.assertEqual(
            [event.pk for event in data.all_events],
            [str(planned.pk), str(completed.pk), str(reviewing.pk)],
        )
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
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
            task_scores={
                '550e8400-e29b-41d4-a716-446655440001': {
                    'points': 1,
                    'max_points': 100,
                },
            },
        )
        capture_attempt_snapshot(mark)
        mark.score = 2
        mark.points = 1
        mark.save(update_fields=['score', 'points'])

        data = GetWorkAnalysisReportUseCase(
            DjangoReportRepository(),
        ).execute(
            WorkAnalysisReportRequest(year=None),
        )
        work_stat = data.works_analysis[0]

        self.assertEqual(work_stat['work'].pk, str(work.pk))
        self.assertEqual(work_stat['work'].name, 'Контрольная')
        self.assertEqual(work_stat['work'].work_type, work.work_type)
        self.assertEqual(
            work_stat['work'].work_type_display,
            work.get_work_type_display(),
        )
        self.assertEqual(work_stat['work'].variant_count, 0)
        self.assertEqual(work_stat['events_count'], 1)
        self.assertEqual(work_stat['events'][0].pk, str(event.pk))
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
        mark = Mark.objects.create(
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
        capture_attempt_snapshot(mark)
        mark.score = 2
        mark.points = 1
        mark.save(update_fields=['score', 'points'])

        data = GetStudentPerformanceReportUseCase(
            DjangoReportRepository(),
        ).execute(
            StudentPerformanceReportRequest(
                year=None,
                group_id=selected_group.pk,
            ),
        )
        stat = data.students_stats[0]

        self.assertEqual(data.selected_group.pk, str(selected_group.pk))
        self.assertEqual(len(data.groups), 2)
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

        data = DjangoReportRepository().get_task_db_health_source()

        self.assertEqual(data.total_tasks, 1)
        self.assertEqual(len(data.group_sizes), 2)
        self.assertEqual(data.total_works, 2)
        self.assertEqual(data.total_variants, 1)
        self.assertEqual(data.orphan_variants_count, 1)
        self.assertEqual(data.orphan_variant_samples[0].number, 1)
        self.assertEqual(
            data.orphan_variant_samples[0].short_uuid,
            Variant.objects.get(work__isnull=True).get_short_uuid(),
        )
        groups_by_id = {item.group.pk: item for item in data.group_sizes}
        self.assertEqual(groups_by_id[str(empty_group.pk)].task_count, 0)
        self.assertEqual(groups_by_id[str(fragile_group.pk)].task_count, 1)
        self.assertEqual(data.coverage[0].work.pk, str(spec_work.pk))
        self.assertEqual(data.coverage[0].work.name, 'Со спецификацией')
        self.assertEqual(
            data.coverage[0].group.pk,
            str(fragile_group.pk),
        )
        self.assertEqual(data.coverage[0].needed, 2)
        self.assertEqual(data.coverage[0].available, 1)
        self.assertEqual(data.ungrouped_tasks_count, 0)
        self.assertEqual(data.works_no_variants_count, 2)
        self.assertEqual(data.works_no_spec_samples[0].pk, str(work_no_spec.pk))
        self.assertEqual(data.difficulty_counts[0].key, 2)
        self.assertEqual(data.difficulty_counts[0].count, 1)
        self.assertEqual(data.type_counts[0].key, 'computational')
        self.assertEqual(data.unverified_tasks_count, 1)
        self.assertEqual(data.no_source_tasks_count, 1)
        self.assertEqual(data.no_grade_tasks_count, 1)
        self.assertEqual(data.courses[0].pk, str(course.pk))

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
        mark = Mark.objects.create(
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
        capture_attempt_snapshot(mark)
        mark.score = 2
        mark.checked_at = now - timedelta(days=60)
        mark.save(update_fields=['score', 'checked_at'])

        data = GetReportsDashboardUseCase(
            DjangoReportRepository(),
        ).execute(
            ReportsDashboardRequest(
                year=None,
                current_date=now,
            ),
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
        self.assertEqual(data.recent_events[0].pk, str(event.pk))
        self.assertEqual(data.recent_events[0].name, 'КР')
        self.assertEqual(data.recent_events[0].status, 'graded')
        self.assertEqual(
            data.recent_events[0].status_display,
            event.get_status_display(),
        )
        self.assertEqual(data.box_data, {'Контрольная': [5]})
        self.assertEqual(data.active_report, 'dashboard')
