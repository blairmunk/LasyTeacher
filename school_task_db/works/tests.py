from django.test import TestCase
from django.urls import reverse

from curriculum.models import Topic
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
