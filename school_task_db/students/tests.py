from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup


class RemedialFromEventViewTests(TestCase):
    """Characterization tests for the current remedial-from-event flow."""

    def setUp(self):
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
        self.source_work = Work.objects.create(
            name='Контрольная по кинематике',
            work_type='test',
            max_score=7,
        )
        self.source_variant = Variant.objects.create(
            work=self.source_work,
            number=1,
            work_name_snapshot=self.source_work.name,
            max_score_snapshot=7,
        )
        self.event = Event.objects.create(
            name='КР 9А',
            work=self.source_work,
            planned_date=timezone.now(),
            status='graded',
        )
        self.participation = EventParticipation.objects.create(
            event=self.event,
            student=self.student,
            variant=self.source_variant,
            status='graded',
        )

        self.weak_original = self._task('Слабое исходное', difficulty=2)
        self.ok_original = self._task('Решённое исходное', difficulty=5)
        self.replacement_easy = self._task('Замена простая', difficulty=3)
        self.replacement_hard = self._task('Замена сложная', difficulty=6)

        self.weak_group = AnalogGroup.objects.create(name='Скорость')
        self.other_group = AnalogGroup.objects.create(name='Графики')
        WorkAnalogGroup.objects.create(
            work=self.source_work,
            analog_group=self.weak_group,
            order=1,
            weight=2,
        )
        TaskGroup.objects.create(task=self.weak_original, group=self.weak_group)
        TaskGroup.objects.create(task=self.replacement_easy, group=self.weak_group)
        TaskGroup.objects.create(task=self.replacement_hard, group=self.weak_group)
        TaskGroup.objects.create(task=self.ok_original, group=self.other_group)

        VariantTask.objects.create(
            variant=self.source_variant,
            task=self.weak_original,
            order=1,
            max_points=2,
            weight=2,
        )
        VariantTask.objects.create(
            variant=self.source_variant,
            task=self.ok_original,
            order=2,
            max_points=5,
            weight=5,
        )

        Mark.objects.create(
            participation=self.participation,
            score=2,
            points=5,
            max_points=7,
            task_scores={
                str(self.weak_original.pk): {'points': 0, 'max_points': 2},
                str(self.ok_original.pk): {'points': 5, 'max_points': 5},
            },
        )

    def _task(self, text, difficulty):
        return Task.objects.create(
            text=text,
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=difficulty,
        )

    def test_get_shows_remedial_preview_analysis_for_event(self):
        response = self.client.get(
            reverse('students:remedial-from-event', args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['event'], self.event)
        self.assertEqual(response.context['work'], self.source_work)
        self.assertEqual(response.context['weak_students'], 1)

        analysis = response.context['analysis']
        self.assertEqual(len(analysis), 1)
        row = analysis[0]
        self.assertEqual(row['student'], self.student)
        self.assertEqual(row['variant'], self.source_variant)
        self.assertEqual(row['score_pct'], 71.4)
        self.assertEqual(row['points'], 5.0)
        self.assertEqual(row['max_points'], 7.0)
        self.assertEqual(row['mark_score'], 2)
        self.assertEqual(row['weak_tasks_count'], 1)
        self.assertEqual(row['weak_tasks'], [str(self.weak_original.pk)])
        self.assertEqual(row['status'], 'weak')

    def test_post_creates_remedial_work_variant_and_event_from_weak_groups(self):
        response = self.client.post(
            reverse('students:remedial-from-event', args=[self.event.pk]),
            {
                'selected_students': [str(self.student.pk)],
                'work_name': 'Работа над ошибками 9А',
                'create_event': '1',
                'event_date': '2026-03-10',
            },
        )

        remedial_work = Work.objects.get(name='Работа над ошибками 9А')
        remedial_variant = Variant.objects.get(
            work=remedial_work,
            assigned_student=self.student,
            variant_type='remedial',
        )
        remedial_event = Event.objects.get(work=remedial_work)
        participation = EventParticipation.objects.get(
            event=remedial_event,
            student=self.student,
        )

        self.assertRedirects(
            response,
            reverse('events:detail', args=[remedial_event.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(remedial_work.work_type, 'remedial')
        self.assertEqual(remedial_work.variant_counter, 1)
        self.assertEqual(remedial_work.max_score, self.replacement_easy.difficulty)
        self.assertEqual(remedial_variant.source_work, self.source_work)
        self.assertEqual(remedial_variant.max_score_snapshot, self.replacement_easy.difficulty)
        self.assertEqual(remedial_event.status, 'planned')
        self.assertEqual(remedial_event.description, f'Работа над ошибками по: {self.source_work.name}')
        self.assertEqual(participation.variant, remedial_variant)
        self.assertEqual(participation.status, 'assigned')

        variant_task = VariantTask.objects.get(variant=remedial_variant)
        self.assertEqual(variant_task.task, self.replacement_easy)
        self.assertEqual(variant_task.order, 1)
        self.assertEqual(variant_task.max_points, self.replacement_easy.difficulty)
        self.assertEqual(variant_task.weight, self.replacement_easy.difficulty)

    def test_post_without_selected_students_redirects_without_creating_remedial_work(self):
        response = self.client.post(
            reverse('students:remedial-from-event', args=[self.event.pk]),
            {
                'work_name': 'Не должна создаться',
                'create_event': '1',
                'event_date': '2026-03-10',
            },
        )

        self.assertRedirects(
            response,
            reverse('students:remedial-from-event', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        self.assertFalse(Work.objects.filter(name='Не должна создаться').exists())

    def test_student_detail_uses_profile_context_from_clean_use_case(self):
        group = StudentGroup.objects.create(name='9А')
        group.students.add(self.student)

        response = self.client.get(reverse('students:detail', args=[self.student.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['student'], self.student)
        self.assertEqual(response.context['student_groups'][0].name, '9А')
        self.assertEqual(response.context['stats']['total_works'], 1)
        self.assertEqual(response.context['stats']['graded_works'], 1)
        self.assertEqual(response.context['stats']['avg_score'], 2)
        self.assertEqual(response.context['stats']['student_level'], 'medium')
        self.assertEqual(response.context['task_log_stats']['total'], 2)
        heatmap_group_names = {
            row['name'] for row in response.context['heatmap_groups']
        }
        self.assertIn('Скорость', heatmap_group_names)
        self.assertEqual(response.context['group_scores'][0]['name'], 'Скорость')
        self.assertEqual(response.context['participations_data'][0].score, 2)
