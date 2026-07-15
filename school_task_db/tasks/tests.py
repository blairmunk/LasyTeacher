import json

from django.test import TestCase
from django.urls import reverse

from curriculum.models import Topic
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work


class TaskBulkGroupAjaxTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name='Механика',
            subject='Физика',
            section='Кинематика',
            grade_level=9,
        )
        self.first_task = Task.objects.create(
            text='Первое задание',
            answer='1',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        self.second_task = Task.objects.create(
            text='Второе задание',
            answer='2',
            topic=self.topic,
            task_type='computational',
            difficulty=3,
        )
        self.group = AnalogGroup.objects.create(name='Существующая группа')

    def post_json(self, url_name, payload):
        return self.client.post(
            reverse(f'tasks:{url_name}'),
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_bulk_create_group_creates_group_with_selected_tasks(self):
        response = self.post_json(
            'bulk-create-group',
            {
                'task_ids': [str(self.first_task.pk), str(self.second_task.pk)],
                'group_name': 'Новая группа',
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        group = AnalogGroup.objects.get(pk=data['group_id'])

        self.assertTrue(data['success'])
        self.assertEqual(data['added'], 2)
        self.assertEqual(group.name, 'Новая группа')
        self.assertEqual(
            TaskGroup.objects.filter(group=group).count(),
            2,
        )

    def test_bulk_add_to_group_adds_only_new_memberships(self):
        TaskGroup.objects.create(task=self.first_task, group=self.group)

        response = self.post_json(
            'bulk-add-to-group',
            {
                'task_ids': [str(self.first_task.pk), str(self.second_task.pk)],
                'group_id': str(self.group.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['added'], 1)
        self.assertEqual(data['skipped'], 1)
        self.assertEqual(
            TaskGroup.objects.filter(group=self.group).count(),
            2,
        )

    def test_bulk_remove_from_groups_removes_selected_task_memberships(self):
        TaskGroup.objects.create(task=self.first_task, group=self.group)
        TaskGroup.objects.create(task=self.second_task, group=self.group)

        response = self.post_json(
            'bulk-remove-from-groups',
            {'task_ids': [str(self.first_task.pk)]},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['removed'], 1)
        self.assertFalse(
            TaskGroup.objects.filter(task=self.first_task, group=self.group).exists()
        )
        self.assertTrue(
            TaskGroup.objects.filter(task=self.second_task, group=self.group).exists()
        )

    def test_bulk_create_work_creates_work_with_first_variant(self):
        response = self.post_json(
            'bulk-create-work',
            {
                'task_ids': [str(self.second_task.pk), str(self.first_task.pk)],
                'work_name': '  Проверочная  ',
                'work_type': 'quiz',
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        work = Work.objects.get(pk=data['work_id'])
        variant = Variant.objects.get(pk=data['variant_id'])
        variant_tasks = list(
            VariantTask.objects.filter(variant=variant).order_by('order')
        )

        self.assertTrue(data['success'])
        self.assertEqual(data['tasks_count'], 2)
        self.assertEqual(data['redirect_url'], f'/works/{work.pk}/')
        self.assertEqual(work.name, 'Проверочная')
        self.assertEqual(work.work_type, 'quiz')
        self.assertEqual(work.variant_counter, 1)
        self.assertEqual(variant.work, work)
        self.assertEqual(
            [variant_task.task for variant_task in variant_tasks],
            [self.second_task, self.first_task],
        )

    def test_task_list_uses_filters_and_context_data(self):
        TaskGroup.objects.create(task=self.first_task, group=self.group)

        response = self.client.get(
            reverse('tasks:list'),
            {
                'search': 'Первое',
                'topic': str(self.topic.pk),
                'group_filter': 'has_group',
                'analog_group': str(self.group.pk),
                'verified': '0',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['tasks']), [self.first_task])
        self.assertEqual(response.context['total_tasks'], 2)
        self.assertEqual(response.context['ungrouped_count'], 1)
        self.assertIn(self.group, list(response.context['analog_groups']))
        self.assertEqual(response.context['current_topic'], str(self.topic.pk))
        self.assertEqual(response.context['current_group_filter'], 'has_group')
