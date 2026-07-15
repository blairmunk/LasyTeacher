from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Topic
from events.models import Event, EventParticipation
from students.models import Student
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup


class WorkDetailViewTests(TestCase):
    def setUp(self):
        self.work = Work.objects.create(
            name='Контрольная',
            work_type='test',
            max_score=5,
        )
        self.topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.variant = Variant.objects.create(
            work=self.work,
            number=1,
            work_name_snapshot=self.work.name,
            max_score_snapshot=5,
        )

    def test_detail_uses_clean_context_data_without_analog_groups(self):
        response = self.client.get(reverse('works:detail', args=[self.work.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['variants'].count(), 1)
        self.assertEqual(response.context['analog_groups'], [])
        self.assertEqual(response.context['spec_preview'], [])
        self.assertTrue(response.context['show_sync_button'])

    def test_detail_uses_clean_context_data_with_spec_preview(self):
        group = AnalogGroup.objects.create(name='Кинематика')
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        TaskGroup.objects.create(task=task, group=group)
        WorkAnalogGroup.objects.create(
            work=self.work,
            analog_group=group,
            count=1,
            weight=2,
            order=1,
        )
        VariantTask.objects.create(
            variant=self.variant,
            task=task,
            order=1,
            max_points=5,
            weight=2,
        )

        response = self.client.get(reverse('works:detail', args=[self.work.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['analog_groups']), 1)
        self.assertEqual(response.context['spec_preview'][0]['wg'].analog_group, group)
        self.assertFalse(response.context['show_sync_button'])

    def test_sync_analog_groups_view_uses_clean_use_case(self):
        group = AnalogGroup.objects.create(name='Кинематика')
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        TaskGroup.objects.create(task=task, group=group)
        VariantTask.objects.create(
            variant=self.variant,
            task=task,
            order=1,
            max_points=5,
            weight=2,
        )

        response = self.client.post(
            reverse('works:sync-groups', args=[self.work.pk])
        )

        self.assertRedirects(
            response,
            reverse('works:detail', args=[self.work.pk]),
            fetch_redirect_response=False,
        )
        groups = WorkAnalogGroup.objects.filter(work=self.work)
        self.assertEqual(groups.count(), 1)
        self.assertEqual(groups[0].analog_group, group)

    def test_generate_variants_view_uses_clean_use_case(self):
        group = AnalogGroup.objects.create(name='Кинематика')
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        TaskGroup.objects.create(task=task, group=group)
        WorkAnalogGroup.objects.create(
            work=self.work,
            analog_group=group,
            count=1,
            weight=2,
            order=1,
        )
        Variant.objects.filter(work=self.work).delete()
        self.work.variant_counter = 0
        self.work.save()

        response = self.client.post(
            reverse('works:generate-variants', args=[self.work.pk]),
            {'count': '2'},
        )

        self.assertRedirects(
            response,
            reverse('works:detail', args=[self.work.pk]),
            fetch_redirect_response=False,
        )
        self.work.refresh_from_db()
        variants = Variant.objects.filter(work=self.work)
        self.assertEqual(variants.count(), 2)
        self.assertEqual(self.work.variant_counter, 2)
        self.assertEqual(variants.first().varianttask_set.count(), 1)

    def test_create_work_from_orphans_view_uses_clean_use_case(self):
        first_orphan = Variant.objects.create(
            work=None,
            number=10,
            work_name_snapshot='Сирота 1',
            variant_type='individual',
        )
        second_orphan = Variant.objects.create(
            work=None,
            number=11,
            work_name_snapshot='Сирота 2',
            variant_type='regular',
        )
        task = Task.objects.create(
            text='Задание для сироты',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=4,
        )
        VariantTask.objects.create(
            variant=first_orphan,
            task=task,
            order=1,
            max_points=4,
            weight=4,
        )
        VariantTask.objects.create(
            variant=second_orphan,
            task=task,
            order=1,
            max_points=2,
            weight=2,
        )

        response = self.client.post(
            reverse('works:create-work-from-orphans'),
            {
                'variant_ids': [str(first_orphan.pk), str(second_orphan.pk)],
                'work_name': '  Индивидуальная подборка  ',
            },
        )

        work = Work.objects.get(name='Индивидуальная подборка')
        self.assertRedirects(
            response,
            reverse('works:detail', args=[work.pk]),
            fetch_redirect_response=False,
        )
        first_orphan.refresh_from_db()
        second_orphan.refresh_from_db()
        self.assertEqual(work.work_type, 'individual')
        self.assertEqual(work.max_score, 4)
        self.assertEqual(work.variant_counter, 2)
        self.assertEqual(first_orphan.work, work)
        self.assertEqual(second_orphan.work, work)
        self.assertEqual(first_orphan.number, 1)
        self.assertEqual(second_orphan.number, 2)

    def test_variant_delete_context_uses_clean_use_case(self):
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        event = Event.objects.create(
            name='КР',
            work=self.work,
            planned_date=timezone.now(),
            status='graded',
        )
        EventParticipation.objects.create(
            event=event,
            student=student,
            variant=self.variant,
            status='graded',
        )
        VariantTask.objects.create(
            variant=self.variant,
            task=Task.objects.create(
                text='Задание',
                answer='Ответ',
                topic=self.topic,
                task_type='computational',
                difficulty=2,
            ),
            order=1,
            max_points=2,
            weight=2,
        )

        response = self.client.get(
            reverse('works:variant-delete', args=[self.variant.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['task_count'], 1)
        self.assertTrue(response.context['has_grades'])
        self.assertEqual(response.context['grade_count'], 1)

    def test_variant_delete_view_blocks_delete_when_variant_has_participations(self):
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        event = Event.objects.create(
            name='КР',
            work=self.work,
            planned_date=timezone.now(),
            status='graded',
        )
        EventParticipation.objects.create(
            event=event,
            student=student,
            variant=self.variant,
            status='graded',
        )

        response = self.client.post(
            reverse('works:variant-delete', args=[self.variant.pk]),
            {'action': 'delete'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Variant.objects.filter(pk=self.variant.pk).exists())

    def test_variant_delete_view_detaches_variant_with_participations(self):
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        event = Event.objects.create(
            name='КР',
            work=self.work,
            planned_date=timezone.now(),
            status='graded',
        )
        EventParticipation.objects.create(
            event=event,
            student=student,
            variant=self.variant,
            status='graded',
        )

        response = self.client.post(
            reverse('works:variant-delete', args=[self.variant.pk]),
            {'action': 'detach'},
        )

        self.assertRedirects(
            response,
            reverse('works:variant-list'),
            fetch_redirect_response=False,
        )
        self.variant.refresh_from_db()
        self.assertIsNone(self.variant.work)

    def test_variant_delete_view_deletes_variant_without_participations(self):
        variant_id = self.variant.pk

        response = self.client.post(
            reverse('works:variant-delete', args=[variant_id]),
            {'action': 'delete'},
        )

        self.assertRedirects(
            response,
            reverse('works:detail', args=[self.work.pk]),
            fetch_redirect_response=False,
        )
        self.assertFalse(Variant.objects.filter(pk=variant_id).exists())
