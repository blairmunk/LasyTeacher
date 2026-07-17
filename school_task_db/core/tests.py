import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import ImportLog
from curriculum.models import Topic
from events.models import Event
from students.models import Student
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Source, Task
from works.models import Variant, Work


class CoreViewsTests(TestCase):
    def test_index_uses_clean_dashboard_summary_context(self):
        topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        work = Work.objects.create(name='Контрольная')
        Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
        )
        Variant.objects.create(
            work=None,
            number=2,
            work_name_snapshot='Сирота',
        )
        Student.objects.create(last_name='Иванов', first_name='Иван')
        Event.objects.create(name='КР', work=work, planned_date=timezone.now())
        AnalogGroup.objects.create(name='Скорость')

        response = self.client.get(reverse('core:index'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['tasks_count'], 1)
        self.assertEqual(response.context['works_count'], 1)
        self.assertEqual(response.context['variants_count'], 2)
        self.assertEqual(response.context['orphan_variants_count'], 1)
        self.assertEqual(response.context['students_count'], 1)
        self.assertEqual(response.context['events_count'], 1)
        self.assertEqual(response.context['groups_count'], 1)

    def test_global_search_returns_text_results_from_clean_use_case(self):
        topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        task = Task.objects.create(
            text='Задача про скорость',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        work = Work.objects.create(name='Контрольная скорость')
        group = AnalogGroup.objects.create(name='скорость')

        response = self.client.get(reverse('core:search'), {'q': 'скорость'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], 'скорость')
        self.assertEqual(response.context['search_mode'], 'text')
        self.assertEqual(response.context['total_found'], 3)
        self.assertEqual(list(response.context['results']['tasks']), [task])
        self.assertEqual(list(response.context['results']['works']), [work])
        self.assertEqual(list(response.context['results']['groups']), [group])
        self.assertEqual(response.context['found_text'], '3 результата')

    def test_global_search_empty_query_returns_empty_context(self):
        response = self.client.get(reverse('core:search'), {'q': '  '})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], '')
        self.assertEqual(response.context['results'], {})
        self.assertEqual(response.context['total_found'], 0)
        self.assertIsNone(response.context['search_mode'])
        self.assertEqual(response.context['found_text'], '')

    def test_import_page_uses_clean_import_page_data(self):
        for index in range(6):
            ImportLog.objects.create(filename=f'import-{index}.json')

        response = self.client.get(reverse('core:import'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['recent_imports']), 5)

    def test_import_history_uses_clean_import_history_data(self):
        first = ImportLog.objects.create(filename='first.json')
        second = ImportLog.objects.create(filename='second.json')

        response = self.client.get(reverse('core:import-history'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['imports']), [second, first])

    def test_validate_import_json_ajax_uses_clean_validation_data(self):
        upload = SimpleUploadedFile(
            'tasks.json',
            json.dumps({'tasks': [{'id': 'bad-uuid', 'text': ''}]}).encode('utf-8'),
            content_type='application/json',
        )

        response = self.client.post(
            reverse('core:import-validate'),
            {'json_file': upload},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['filename'], 'tasks.json')
        self.assertFalse(payload['validation']['is_valid'])
        self.assertEqual(
            payload['validation']['errors'],
            [
                'Задание #1: некорректный UUID "bad-uuid"',
                'Задание #1: отсутствует text',
            ],
        )
        self.assertIsNone(payload['preview'])

    def test_execute_import_json_ajax_uses_clean_import_use_case(self):
        upload = SimpleUploadedFile(
            'tasks.json',
            json.dumps({
                'tasks': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'text': 'Задача на силу',
                        'answer': 'Ответ',
                        'task_type': 'computational',
                        'difficulty': 2,
                        'topic': {
                            'name': 'Динамика',
                            'subject': 'Физика',
                            'grade_level': 9,
                        },
                    },
                ],
            }).encode('utf-8'),
            content_type='application/json',
        )

        response = self.client.post(
            reverse('core:import-execute'),
            {
                'json_file': upload,
                'mode': 'update',
                'dry_run': 'false',
                'create_missing': 'true',
            },
        )
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['status'], 'success')
        self.assertEqual(payload['stats']['created'], 1)
        self.assertEqual(payload['stats']['context_counts']['tasks'], 1)
        self.assertTrue(Task.objects.filter(text='Задача на силу').exists())
        self.assertTrue(ImportLog.objects.filter(pk=payload['log_id']).exists())

    def test_export_tasks_returns_clean_export_payload(self):
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        source = Source.objects.create(name='Сборник', short_name='Сб.')
        task = Task.objects.create(
            text='Задача на силу',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
            source=source,
        )
        group = AnalogGroup.objects.create(name='Силы')
        TaskGroup.objects.create(task=task, group=group)

        response = self.client.get(
            reverse('core:export'),
            {'subject': 'Физика', 'grade': '9'},
        )
        payload = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertTrue(
            response['Content-Disposition'].startswith('attachment; filename="export_'),
        )
        self.assertEqual(payload['version'], '1.1')
        self.assertEqual(len(payload['tasks']), 1)
        self.assertEqual(payload['tasks'][0]['id'], str(task.pk))
        self.assertEqual(payload['tasks'][0]['groups'], [str(group.pk)])
        self.assertEqual(payload['topics'][0]['name'], topic.name)
        self.assertEqual(payload['sources'][0]['id'], str(source.pk))
