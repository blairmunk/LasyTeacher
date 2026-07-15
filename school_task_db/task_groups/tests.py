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
