from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student
from tasks.models import Task
from works.models import Variant, VariantTask, Work


class GradeParticipationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher',
            password='pass',
            first_name='Мария',
            last_name='Иванова',
        )
        self.client.login(username='teacher', password='pass')

        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        self.work = Work.objects.create(name='Контрольная', work_type='test')
        self.variant = Variant.objects.create(
            work=self.work,
            number=1,
            work_name_snapshot=self.work.name,
        )
        self.task = Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        VariantTask.objects.create(
            variant=self.variant,
            task=self.task,
            order=1,
            max_points=2,
            weight=2,
        )
        self.event = Event.objects.create(
            name='КР 9Б',
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
        self.mark = Mark.objects.create(
            participation=self.participation,
            task_scores={str(self.task.pk): {'points': 0, 'max_points': 2}},
        )

    def test_post_grades_participation_without_wiping_existing_task_scores(self):
        response = self.client.post(
            reverse('events:grade-participation', args=[self.participation.pk]),
            {
                'score': '3',
                'points': '1',
                'max_points': '2',
                'teacher_comment': 'Есть ошибки',
                'mistakes_analysis': 'Нужно повторить',
                'recommendations': 'Решить ещё',
            },
        )

        self.assertRedirects(
            response,
            reverse('events:review-works'),
            fetch_redirect_response=False,
        )

        self.mark.refresh_from_db()
        self.participation.refresh_from_db()
        self.event.refresh_from_db()

        self.assertEqual(self.mark.score, 3)
        self.assertEqual(self.mark.points, 1)
        self.assertEqual(self.mark.max_points, 2)
        self.assertEqual(self.mark.teacher_comment, 'Есть ошибки')
        self.assertEqual(self.mark.mistakes_analysis, 'Нужно повторить')
        self.assertEqual(self.mark.recommendations, 'Решить ещё')
        self.assertEqual(self.mark.checked_by, 'Мария Иванова')
        self.assertEqual(
            self.mark.task_scores,
            {str(self.task.pk): {'points': 0, 'max_points': 2}},
        )
        self.assertEqual(self.participation.status, 'graded')
        self.assertEqual(self.event.status, 'completed')

    def test_event_list_uses_clean_context_categories(self):
        response = self.client.get(reverse('events:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['events']), 1)
        self.assertEqual(len(response.context['active_events']), 1)
        self.assertEqual(response.context['active_events'][0], self.event)
        self.assertEqual(response.context['events'][0].participant_count, 1)

    def test_event_detail_uses_clean_context_data(self):
        response = self.client.get(reverse('events:detail', args=[self.event.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['event'], self.event)
        self.assertTrue(response.context['some_variants_assigned'])
        self.assertTrue(response.context['all_variants_assigned'])
        self.assertTrue(response.context['can_review'])
        self.assertEqual(response.context['status_color'], 'info')
        self.assertEqual(response.context['status_steps'][2].code, 'completed')
        self.assertEqual(response.context['status_transitions'][0].new_status, 'reviewing')
        self.assertEqual(response.context['participations'][0].student.last_name, 'Петров')
        self.assertEqual(response.context['participations'][0].variant.number, 1)
        self.assertEqual(response.context['participations'][0].mark_obj.score, None)
        self.assertEqual(response.context['available_variants'][0].number, 1)
