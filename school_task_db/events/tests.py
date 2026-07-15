import datetime as dt

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
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
            reverse('review:dashboard'),
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

    def test_review_works_legacy_route_redirects_to_review_dashboard(self):
        response = self.client.get(reverse('events:review-works'))

        self.assertRedirects(
            response,
            reverse('review:dashboard'),
            fetch_redirect_response=False,
        )

    def test_grade_participation_get_redirects_to_current_review_screen(self):
        response = self.client.get(
            reverse('events:grade-participation', args=[self.participation.pk])
        )

        self.assertRedirects(
            response,
            reverse('review:participation-review', args=[self.participation.pk]),
            fetch_redirect_response=False,
        )

    def test_grade_participation_get_does_not_create_empty_mark(self):
        participation = EventParticipation.objects.create(
            event=self.event,
            student=Student.objects.create(last_name='Смирнов', first_name='Семён'),
            variant=self.variant,
            status='completed',
        )

        response = self.client.get(
            reverse('events:grade-participation', args=[participation.pk])
        )

        self.assertRedirects(
            response,
            reverse('review:participation-review', args=[participation.pk]),
            fetch_redirect_response=False,
        )
        self.assertFalse(Mark.objects.filter(participation=participation).exists())

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

    def test_event_create_adds_selected_group_participants_through_use_case(self):
        group = StudentGroup.objects.create(name='9Б')
        group.students.add(self.student)

        response = self.client.post(
            reverse('events:create'),
            {
                'name': 'Новая КР',
                'work': str(self.work.pk),
                'planned_date': '2026-03-10T09:00',
                'status': 'planned',
                'student_group': str(group.pk),
            },
        )
        event = Event.objects.get(name='Новая КР')

        self.assertRedirects(
            response,
            reverse('events:detail', args=[event.pk]),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            EventParticipation.objects.filter(
                event=event,
                student=self.student,
                status='assigned',
            ).exists()
        )

    def test_add_participants_view_uses_clean_use_case(self):
        second_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )

        response = self.client.post(
            reverse('events:add-participants', args=[self.event.pk]),
            {
                'individual_students': [str(second_student.pk)],
            },
        )

        self.assertRedirects(
            response,
            reverse('events:detail', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            EventParticipation.objects.filter(
                event=self.event,
                student=second_student,
                status='assigned',
            ).exists()
        )

    def test_add_participants_view_uses_clean_selection_context(self):
        response = self.client.get(
            reverse('events:add-participants', args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 200)
        current_participants = response.context['current_participants']
        self.assertEqual(len(current_participants), 1)
        self.assertEqual(current_participants[0].student.last_name, 'Петров')

    def test_assign_variants_view_uses_clean_use_case(self):
        second_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
        )

        response = self.client.post(
            reverse('events:assign-variants', args=[self.event.pk]),
            {
                f'variant_{self.participation.pk}': str(second_variant.pk),
            },
        )

        self.assertRedirects(
            response,
            reverse('events:detail', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.variant, second_variant)

    def test_assign_variants_view_uses_clean_assignment_form_data(self):
        second_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
        )

        response = self.client.get(
            reverse('events:assign-variants', args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 200)
        field = response.context['form'].fields[f'variant_{self.participation.pk}']
        self.assertIn((str(second_variant.pk), 'Вариант 2'), field.choices)

    def test_assign_single_variant_view_uses_clean_use_case(self):
        second_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
        )

        response = self.client.post(
            reverse('events:assign-single-variant', args=[self.event.pk]),
            {
                'participation_id': str(self.participation.pk),
                'variant_id': str(second_variant.pk),
            },
        )

        self.assertRedirects(
            response,
            reverse('events:detail', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.variant, second_variant)

    def test_assign_single_variant_view_returns_404_for_missing_event(self):
        response = self.client.post(
            reverse(
                'events:assign-single-variant',
                args=['00000000-0000-0000-0000-000000000000'],
            ),
            {
                'participation_id': str(self.participation.pk),
                'variant_id': str(self.variant.pk),
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_change_status_view_uses_clean_use_case(self):
        response = self.client.post(
            reverse('events:change-status', args=[self.event.pk]),
            {
                'new_status': 'reviewing',
            },
        )

        self.assertRedirects(
            response,
            reverse('events:detail', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, 'reviewing')

    def test_change_status_view_returns_404_for_missing_event(self):
        response = self.client.post(
            reverse(
                'events:change-status',
                args=['00000000-0000-0000-0000-000000000000'],
            ),
            {
                'new_status': 'reviewing',
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_event_update_form_shows_existing_date_without_time_input(self):
        self.event.planned_date = timezone.make_aware(
            dt.datetime(2026, 3, 10, 14, 30),
        )
        self.event.save()

        response = self.client.get(reverse('events:update', args=[self.event.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="date"')
        self.assertContains(response, 'value="2026-03-10"')
        self.assertNotContains(response, 'type="datetime-local"')

    def test_event_update_accepts_date_only_and_sets_default_time(self):
        response = self.client.post(
            reverse('events:update', args=[self.event.pk]),
            {
                'name': self.event.name,
                'work': str(self.work.pk),
                'planned_date': '2026-03-11',
                'status': self.event.status,
                'description': self.event.description,
                'location': self.event.location,
            },
        )

        self.assertRedirects(
            response,
            reverse('events:list'),
            fetch_redirect_response=False,
        )
        self.event.refresh_from_db()
        planned_date = timezone.localtime(self.event.planned_date)
        self.assertEqual(planned_date.date(), dt.date(2026, 3, 11))
        self.assertEqual(planned_date.time().replace(tzinfo=None), dt.time(9, 0))
