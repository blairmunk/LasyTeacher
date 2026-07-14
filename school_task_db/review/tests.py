from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Topic
from events.models import Event, EventParticipation, Mark
from review.models import ReviewComment
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
        self.next_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )
        self.next_participation = EventParticipation.objects.create(
            event=self.event,
            student=self.next_student,
            variant=self.variant,
            status='completed',
        )

    def test_get_uses_participation_review_context_from_clean_use_case(self):
        ReviewComment.objects.create(
            text='Проверь оформление',
            category='suggestion',
            usage_count=5,
        )

        response = self.client.get(
            reverse('review:participation-review', args=[self.participation.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['participation'].pk, str(self.participation.pk))
        self.assertEqual(response.context['participation'].student.last_name, 'Иванов')
        self.assertEqual(response.context['mark'].max_points, 2)
        self.assertEqual(len(response.context['tasks_with_scores']), 1)
        self.assertEqual(response.context['tasks_with_scores'][0].task.text, 'Найти скорость')
        self.assertEqual(response.context['tasks_with_scores'][0].max_points, 2)
        self.assertEqual(response.context['typical_comments'][0].text, 'Проверь оформление')
        self.assertIsNone(response.context['previous_participation'])
        self.assertEqual(
            response.context['next_participation'].pk,
            str(self.next_participation.pk),
        )
        self.assertEqual(response.context['current_position'], 1)
        self.assertEqual(response.context['total_positions'], 2)
        self.assertEqual(response.context['navigation_progress'], 50)

    def test_dashboard_uses_review_summary_from_clean_use_case(self):
        response = self.client.get(reverse('review:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_events'], 1)
        self.assertEqual(len(response.context['needs_review']), 1)
        self.assertEqual(response.context['needs_review'][0].event.name, 'КР 9А')
        self.assertEqual(response.context['needs_review'][0].active_participants, 2)
        self.assertEqual(response.context['needs_review'][0].remaining, 2)

    def test_event_review_uses_event_review_context_from_clean_use_case(self):
        response = self.client.get(reverse('review:event-review', args=[self.event.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['blocked'])
        self.assertTrue(response.context['has_participants'])
        self.assertTrue(response.context['variants_assigned'])
        self.assertTrue(response.context['all_variants_assigned'])
        self.assertEqual(response.context['total_participants'], 2)
        self.assertEqual(response.context['active_participants'], 2)
        self.assertEqual(response.context['graded_participants'], 0)
        self.assertEqual(response.context['progress_percentage'], 0)
        self.assertEqual(len(response.context['participations_data']), 2)
        self.assertEqual(response.context['participations_data'][0].variant.tasks.count, 1)
        self.assertEqual(response.context['available_variants'][0].number, 1)

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
        self.assertEqual(self.event.status, 'reviewing')
        self.assertEqual(task_log.percentage, 100)

    def test_ajax_calculate_score_uses_clean_use_case(self):
        response = self.client.get(
            reverse('review:ajax-calculate-score'),
            {'points': '8', 'max_points': '10'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {'score': 4, 'percentage': 80.0},
        )

    def test_ajax_calculate_score_tolerates_empty_values(self):
        response = self.client.get(
            reverse('review:ajax-calculate-score'),
            {'points': '', 'max_points': ''},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {'score': 2, 'percentage': 0},
        )

    def test_finalize_event_uses_clean_use_case(self):
        response = self.client.post(
            reverse('review:finalize-event', args=[self.event.pk])
        )

        self.assertRedirects(
            response,
            reverse('review:event-review', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, 'graded')

    def test_toggle_absent_uses_clean_use_case(self):
        response = self.client.post(
            reverse('review:toggle-absent', args=[self.participation.pk])
        )

        self.assertRedirects(
            response,
            reverse('review:event-review', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.status, 'absent')
