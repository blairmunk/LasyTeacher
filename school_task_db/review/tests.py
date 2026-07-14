from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentTaskLog
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work


class ParticipationReviewViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher',
            password='pass',
            first_name='Мария',
            last_name='Иванова',
        )
        self.client.login(username='teacher', password='pass')

        self.topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        self.work = Work.objects.create(name='Контрольная', work_type='test')
        self.variant = Variant.objects.create(
            work=self.work,
            number=1,
            work_name_snapshot=self.work.name,
        )
        self.task = Task.objects.create(
            text='Найти скорость',
            answer='10 м/с',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        self.group = AnalogGroup.objects.create(name='Скорость')
        TaskGroup.objects.create(task=self.task, group=self.group)
        VariantTask.objects.create(
            variant=self.variant,
            task=self.task,
            order=1,
            max_points=2,
            weight=2,
        )
        self.event = Event.objects.create(
            name='КР 9А',
            work=self.work,
            planned_date=timezone.now(),
            status='completed',
        )
        self.participation = EventParticipation.objects.create(
            event=self.event,
            student=self.student,
            variant=self.variant,
            status='completed',
        )

    def test_post_grades_participation_through_use_case(self):
        response = self.client.post(
            reverse('review:participation-review', args=[self.participation.pk]),
            {
                'score': '4',
                'points': '2',
                'max_points': '2',
                'teacher_comment': 'Хорошо',
                f'task_{self.task.pk}': '2',
                f'task_{self.task.pk}_max': '2',
                f'task_{self.task.pk}_comment': 'Верно',
            },
        )

        self.assertRedirects(
            response,
            reverse('review:event-review', args=[self.event.pk]),
            fetch_redirect_response=False,
        )

        mark = Mark.objects.get(participation=self.participation)
        self.participation.refresh_from_db()
        self.event.refresh_from_db()
        task_log = StudentTaskLog.objects.get(
            student=self.student,
            task=self.task,
            event=self.event,
        )

        self.assertEqual(mark.score, 4)
        self.assertEqual(mark.points, 2)
        self.assertEqual(mark.max_points, 2)
        self.assertEqual(mark.teacher_comment, 'Хорошо')
        self.assertEqual(mark.checked_by, 'Мария Иванова')
        self.assertEqual(
            mark.task_scores,
            {str(self.task.pk): {'points': 2, 'max_points': 2, 'comment': 'Верно'}},
        )
        self.assertEqual(self.participation.status, 'graded')
        self.assertEqual(self.event.status, 'graded')
        self.assertEqual(task_log.percentage, 100)
