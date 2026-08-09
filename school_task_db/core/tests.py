import json
from datetime import date
from importlib import import_module
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import AcademicYear, ImportLog
from core.test_slices import TEST_SLICES
from core.importers.tasks import TaskImporter
from curriculum.models import Course, Topic
from events.models import AttemptTaskSnapshot, Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Source, Task
from works.models import Variant, Work
from core.management.commands.html_to_pdf import (
    html_to_pdf_file_pairs,
    is_valid_html_file,
    output_pdf_path,
)


class CoreViewsTests(TestCase):
    def test_html_to_pdf_command_rejects_missing_path(self):
        with self.assertRaises(CommandError):
            call_command('html_to_pdf', 'missing.html')

    def test_html_to_pdf_helpers_build_valid_file_pairs(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            valid_html = temp_path / 'valid.html'
            invalid_html = temp_path / 'invalid.html'
            valid_html.write_text(
                '<html><head></head><body>OK</body></html>',
                encoding='utf-8',
            )
            invalid_html.write_text('<div>bad</div>', encoding='utf-8')

            pairs = html_to_pdf_file_pairs(
                [valid_html, invalid_html],
                temp_path / 'pdf',
            )

            self.assertTrue(is_valid_html_file(valid_html))
            self.assertFalse(is_valid_html_file(invalid_html))
            self.assertEqual(
                pairs,
                [(valid_html, temp_path / 'pdf' / 'valid.pdf')],
            )
            self.assertEqual(
                output_pdf_path(valid_html, temp_path / 'pdf'),
                temp_path / 'pdf' / 'valid.pdf',
            )

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
        self.assertEqual(response.context['results']['tasks'][0].pk, str(task.pk))
        self.assertEqual(response.context['results']['works'][0].pk, str(work.pk))
        self.assertEqual(response.context['results']['groups'][0].pk, str(group.pk))
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
        self.assertEqual(response.context['imports'][0].filename, second.filename)
        self.assertEqual(response.context['imports'][1].filename, first.filename)

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

    def test_validate_import_json_ajax_uses_clean_preview_data(self):
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
            reverse('core:import-validate'),
            {'json_file': upload},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['validation']['is_valid'])
        self.assertEqual(payload['preview']['total_created'], 0)
        self.assertEqual(payload['preview']['tasks_in_context'], 0)
        self.assertFalse(Task.objects.filter(text='Задача на силу').exists())

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

    def test_task_importer_persists_and_updates_group_bank_role(self):
        group_id = '770e8400-e29b-41d4-a716-446655440001'
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = {
            'analog_groups': [
                {
                    'id': group_id,
                    'name': 'Группа для демонстрации',
                    'difficulty': 3,
                },
            ],
            'topics': [
                {
                    'name': 'Динамика',
                    'subject': 'Физика',
                    'grade_level': 9,
                    'section': 'Механика',
                },
            ],
            'tasks': [
                {
                    'id': task_id,
                    'text': 'Найдите ускорение.',
                    'answer': '2 м/с²',
                    'task_type': 'computational',
                    'difficulty': 2,
                    'topic': {
                        'name': 'Динамика',
                        'subject': 'Физика',
                        'grade_level': 9,
                    },
                    'groups': [
                        {
                            'id': group_id,
                            'bank_role': 'demo',
                        },
                    ],
                },
            ],
        }

        TaskImporter(mode='update', create_missing=True).import_tasks_from_json(
            payload,
        )

        relation = TaskGroup.objects.get(
            task_id=task_id,
            group_id=group_id,
        )
        self.assertEqual(relation.bank_role, 'demo')
        self.assertEqual(relation.group.difficulty, 3)

        payload['tasks'][0]['groups'][0]['bank_role'] = 'practice'
        payload['analog_groups'][0]['difficulty'] = 4
        TaskImporter(mode='update', create_missing=True).import_tasks_from_json(
            payload,
        )

        relation.refresh_from_db()
        relation.group.refresh_from_db()
        self.assertEqual(relation.bank_role, 'practice')
        self.assertEqual(relation.group.difficulty, 4)

    def test_task_importer_dry_run_accepts_group_role_objects(self):
        output = []
        payload = {
            'analog_groups': [
                {
                    'id': '770e8400-e29b-41d4-a716-446655440001',
                    'name': 'Группа',
                },
            ],
            'tasks': [
                {
                    'id': '550e8400-e29b-41d4-a716-446655440001',
                    'text': 'Задача',
                    'groups': [
                        {
                            'id': '770e8400-e29b-41d4-a716-446655440001',
                            'bank_role': 'demo',
                        },
                    ],
                },
            ],
        }

        TaskImporter(
            mode='update',
            dry_run=True,
            create_missing=True,
            output=output.append,
        ).import_tasks_from_json(payload)

        self.assertIn('🔍 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР (--dry-run)', output)

    def test_import_tasks_command_uses_clean_import_service(self):
        payload = {
            'topics': [
                {
                    'name': 'Динамика',
                    'subject': 'Физика',
                    'grade_level': 9,
                    'section': 'Механика',
                },
            ],
            'tasks': [
                {
                    'id': '550e8400-e29b-41d4-a716-446655440011',
                    'text': 'Задача из management-команды',
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
        }

        with TemporaryDirectory() as temp_dir:
            json_file = Path(temp_dir) / 'tasks.json'
            json_file.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding='utf-8',
            )
            output = StringIO()

            call_command(
                'import_tasks',
                str(json_file),
                create_topics=True,
                stdout=output,
            )

        self.assertTrue(
            Task.objects.filter(
                text='Задача из management-команды',
            ).exists(),
        )
        log = ImportLog.objects.get(filename='tasks.json')
        self.assertEqual(log.status, ImportLog.Status.SUCCESS)
        self.assertIn('ИМПОРТ ЗАВЕРШЁН', output.getvalue())

    def test_import_tasks_command_uses_clean_json_validation(self):
        with TemporaryDirectory() as temp_dir:
            json_file = Path(temp_dir) / 'broken.json'
            json_file.write_text('{broken', encoding='utf-8')

            with self.assertRaisesRegex(CommandError, 'Невалидный JSON'):
                call_command('import_tasks', str(json_file))

    def test_build_test_scenario_is_idempotent_and_builds_learning_logs(self):
        year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 1),
            end_date=date(2027, 8, 31),
            is_active=True,
        )
        student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        student_group = StudentGroup.objects.create(
            name='7А',
            academic_year=year,
        )
        student_group.students.add(student)
        topic = Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Механика',
            grade_level=7,
        )
        task = Task.objects.create(
            text='Найдите скорость.',
            answer='5 м/с',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        group = AnalogGroup.objects.create(name='Скорость — контроль')
        TaskGroup.objects.create(
            task=task,
            group=group,
            bank_role='control',
        )
        manifest = {
            'namespace': 'cc8e6d24-5d9b-4b4c-b0da-71cc6532aff6',
            'academic_year': year.name,
            'courses': [
                {
                    'key': 'physics-7',
                    'name': 'Физика 7',
                    'grade_level': 7,
                    'student_groups': ['7А'],
                },
            ],
            'works': [
                {
                    'key': 'speed-work',
                    'name': 'Работа по скорости',
                    'variant_count': 1,
                    'specification': [
                        {
                            'analog_group_id': str(group.pk),
                            'order': 1,
                            'count': 1,
                            'weight': 1,
                            'bank_role_filter': 'control',
                        },
                    ],
                    'course_assignment': {
                        'course': 'physics-7',
                    },
                },
            ],
            'events': [
                {
                    'key': 'graded-speed',
                    'name': 'Проверенная работа',
                    'work': 'speed-work',
                    'course': 'physics-7',
                    'student_group': '7А',
                    'planned_date': '2026-09-15T09:00:00',
                    'status': 'graded',
                    'graded_count': 1,
                },
            ],
        }

        with TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / 'scenario.json'
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding='utf-8',
            )
            call_command('build_test_scenario', str(manifest_path))
            call_command('build_test_scenario', str(manifest_path))

        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Work.objects.count(), 1)
        self.assertEqual(Variant.objects.count(), 1)
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(EventParticipation.objects.count(), 1)
        self.assertEqual(Mark.objects.count(), 1)
        task_result = AttemptTaskSnapshot.objects.get()
        self.assertEqual(task_result.attempt.student_id_snapshot, str(student.pk))
        self.assertEqual(task_result.task_id_snapshot, str(task.pk))
        self.assertIsNotNone(task_result.variant_task)

    def test_download_sample_json_uses_clean_sample_data(self):
        response = self.client.get(reverse('core:import-sample'))
        payload = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="sample_import.json"',
        )
        self.assertEqual(payload['version'], '1.2')
        self.assertEqual(len(payload['tasks']), 2)
        self.assertEqual(payload['task_images'], [])

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
        self.assertEqual(payload['version'], '1.2')
        self.assertEqual(len(payload['tasks']), 1)
        self.assertEqual(payload['tasks'][0]['id'], str(task.pk))
        self.assertEqual(
            payload['tasks'][0]['groups'],
            [{'id': str(group.pk), 'bank_role': 'control'}],
        )
        self.assertEqual(payload['topics'][0]['name'], topic.name)
        self.assertEqual(payload['sources'][0]['id'], str(source.pk))


class TestSliceCommandTests(TestCase):
    def test_every_configured_label_is_importable(self):
        for slice_name, labels in TEST_SLICES.items():
            for label in labels:
                with self.subTest(slice=slice_name, label=label):
                    import_module(label)

    def test_list_prints_available_slices(self):
        output = StringIO()

        call_command('test_slice', '--list', stdout=output)

        self.assertIn('reports', output.getvalue())
        self.assertIn('documents', output.getvalue())
        self.assertIn('all', output.getvalue())

    def test_named_slice_delegates_to_django_test_command(self):
        output = StringIO()

        with patch(
            'core.management.commands.test_slice.call_command',
        ) as test_command:
            call_command(
                'test_slice',
                'reports',
                keepdb=True,
                failfast=True,
                stdout=output,
            )

        args, kwargs = test_command.call_args
        self.assertEqual(args[0], 'test')
        self.assertEqual(args[1:], TEST_SLICES['reports'])
        self.assertTrue(kwargs['keepdb'])
        self.assertTrue(kwargs['failfast'])
        self.assertFalse(kwargs['interactive'])
