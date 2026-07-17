import json

from django.test import TestCase
from django.urls import reverse

from curriculum.models import Topic
from tasks.models import Task
from task_groups.models import AnalogGroup, TaskGroup
from works.models import Work, WorkAnalogGroup


class TaskGroupBulkActionTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.group = AnalogGroup.objects.create(name='Скорость')
        self.task = Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=4,
        )
        TaskGroup.objects.create(task=self.task, group=self.group)

    def test_bulk_create_work_from_groups_uses_clean_use_case(self):
        response = self.client.post(
            reverse('task_groups:bulk-create-work'),
            data=json.dumps({
                'groups': [
                    {
                        'id': str(self.group.pk),
                        'order': 1,
                        'count': 2,
                        'weight': 0,
                    }
                ],
                'work_name': '  Контрольная по кинематике  ',
                'work_type': 'quiz',
                'max_score': 10,
                'auto_generate': False,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        work = Work.objects.get(name='Контрольная по кинематике')
        spec = WorkAnalogGroup.objects.get(work=work)
        self.assertEqual(work.work_type, 'quiz')
        self.assertEqual(work.max_score, 10)
        self.assertEqual(spec.analog_group, self.group)
        self.assertEqual(spec.count, 2)
        self.assertEqual(spec.weight, 4)
        self.assertEqual(response.json()['work_id'], str(work.pk))

    def test_analog_group_list_uses_clean_list_context(self):
        response = self.client.get(
            reverse('task_groups:list'),
            {
                'search': 'Скор',
                'topic': str(self.topic.pk),
                'difficulty': '4',
                'group_filter': 'nonempty',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['analog_groups']), [self.group])
        self.assertEqual(response.context['topics'][0], self.topic)
        self.assertEqual(response.context['total_groups'], 1)
        self.assertEqual(response.context['empty_groups'], 0)
        self.assertEqual(response.context['total_tasks_in_groups'], 1)

    def test_analog_group_detail_uses_clean_detail_context(self):
        response = self.client.get(reverse('task_groups:detail', args=[self.group.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['analoggroup'].pk, str(self.group.pk))
        self.assertEqual(response.context['analoggroup'].name, self.group.name)
        self.assertEqual(response.context['tasks'][0].pk, str(self.task.pk))
        self.assertEqual(response.context['tasks'][0].text, self.task.text)

    def test_analog_group_detail_returns_404_for_missing_group(self):
        response = self.client.get(
            reverse(
                'task_groups:detail',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_add_tasks_to_group_get_uses_clean_form_context(self):
        second_task = Task.objects.create(
            text='Вторая задача',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=3,
        )

        response = self.client.get(
            reverse('task_groups:add-tasks', args=[self.group.pk]),
            {'search': 'Вторая'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(list(response.context['available_tasks']), [second_task])
        self.assertEqual(response.context['search'], 'Вторая')

    def test_bulk_create_work_from_groups_rejects_missing_groups(self):
        response = self.client.post(
            reverse('task_groups:bulk-create-work'),
            data=json.dumps({
                'groups': [
                    {
                        'id': '00000000-0000-0000-0000-000000000000',
                        'order': 1,
                        'count': 1,
                        'weight': 1,
                    }
                ],
                'work_name': 'Контрольная',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Некоторые группы не найдены'})

    def test_bulk_delete_groups_uses_clean_use_case(self):
        second_group = AnalogGroup.objects.create(name='Ускорение')

        response = self.client.post(
            reverse('task_groups:bulk-delete'),
            data=json.dumps({
                'group_ids': [str(self.group.pk), str(second_group.pk)],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['deleted'], 2)
        self.assertFalse(AnalogGroup.objects.filter(pk=self.group.pk).exists())
        self.assertFalse(AnalogGroup.objects.filter(pk=second_group.pk).exists())

    def test_bulk_delete_groups_rejects_empty_selection(self):
        response = self.client.post(
            reverse('task_groups:bulk-delete'),
            data=json.dumps({'group_ids': []}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Не выбрано ни одной группы'})

    def test_add_tasks_to_group_post_uses_clean_use_case(self):
        second_task = Task.objects.create(
            text='Вторая задача',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=3,
        )

        response = self.client.post(
            reverse('task_groups:add-tasks', args=[self.group.pk]),
            {'selected_tasks': [str(second_task.pk)]},
        )

        self.assertRedirects(
            response,
            reverse('task_groups:detail', args=[self.group.pk]),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            TaskGroup.objects.filter(group=self.group, task=second_task).exists()
        )

    def test_remove_task_from_group_post_uses_clean_use_case(self):
        response = self.client.post(
            reverse(
                'task_groups:remove-task',
                args=[self.group.pk, self.task.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse('task_groups:detail', args=[self.group.pk]),
            fetch_redirect_response=False,
        )
        self.assertFalse(
            TaskGroup.objects.filter(group=self.group, task=self.task).exists()
        )
