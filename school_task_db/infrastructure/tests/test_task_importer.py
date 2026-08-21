import base64
from tempfile import TemporaryDirectory

from django.test import TestCase

from codifier.models import CodifierSpec, ContentEntry, Requirement
from infrastructure.importers.tasks import TaskImporter
from task_groups.models import TaskGroup
from tasks.models import Source, Task, TaskImage


class TaskImporterTests(TestCase):
    def test_imports_portable_explicit_classifications(self):
        codifier = CodifierSpec.objects.create(
            name='ОГЭ по физике 2026',
            short_name='ОГЭ 2026',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        content_entry = ContentEntry.objects.create(
            codifier=codifier,
            code='1.1',
            name='Динамика',
        )
        requirement = Requirement.objects.create(
            codifier=codifier,
            code='2.1',
            name='Решать задачи',
        )
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(
            task_id=task_id,
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        reference = {
            'subject': 'Физика',
            'exam_type': 'oge',
            'year': 2026,
        }
        payload['tasks'][0]['codifier_content_entries'] = [
            {**reference, 'code': '1.1'},
        ]
        payload['tasks'][0]['codifier_requirements'] = [
            {**reference, 'code': '2.1'},
        ]

        self._import(payload)

        task = Task.objects.get(pk=task_id)
        self.assertEqual(
            list(task.codifier_content_entries.all()),
            [content_entry],
        )
        self.assertEqual(
            list(task.codifier_requirements.all()),
            [requirement],
        )

        payload['tasks'][0]['codifier_content_entries'] = []
        payload['tasks'][0].pop('codifier_requirements')
        self._import(payload)
        task.refresh_from_db()
        self.assertFalse(task.codifier_content_entries.exists())
        self.assertEqual(
            list(task.codifier_requirements.all()),
            [requirement],
        )

    def test_low_level_import_ignores_removed_legacy_classification_fields(self):
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(
            task_id=task_id,
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        payload['tasks'][0].update({
            'content_element': '1.2',
            'requirement_element': '2.1',
        })

        self._import(payload)

        task = Task.objects.get(pk=task_id)
        self.assertFalse(hasattr(task, 'content_element'))
        self.assertFalse(hasattr(task, 'requirement_element'))
        self.assertFalse(task.codifier_content_entries.exists())
        self.assertFalse(task.codifier_requirements.exists())

    def test_persists_and_updates_group_bank_role(self):
        group_id = '770e8400-e29b-41d4-a716-446655440001'
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(task_id=task_id, group_id=group_id)

        self._import(payload)

        relation = TaskGroup.objects.get(
            task_id=task_id,
            group_id=group_id,
        )
        self.assertEqual(relation.bank_role, 'demo')
        self.assertEqual(relation.group.difficulty, 3)

        payload['tasks'][0]['groups'][0]['bank_role'] = 'practice'
        payload['analog_groups'][0]['difficulty'] = 4
        self._import(payload)

        relation.refresh_from_db()
        relation.group.refresh_from_db()
        self.assertEqual(relation.bank_role, 'practice')
        self.assertEqual(relation.group.difficulty, 4)

    def test_group_name_fallback_creates_group_and_membership(self):
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(
            task_id=task_id,
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        payload.pop('analog_groups')
        payload['tasks'][0].pop('groups')
        payload['tasks'][0]['group_name'] = 'Группа по имени'

        self._import(payload)

        relation = TaskGroup.objects.select_related('group').get(
            task_id=task_id,
        )
        self.assertEqual(relation.group.name, 'Группа по имени')
        self.assertEqual(relation.bank_role, 'control')

    def test_existing_task_record_is_updated(self):
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(
            task_id=task_id,
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        self._import(payload)

        payload['tasks'][0].update({
            'text': 'Обновлённое условие',
            'answer': 'Новый ответ',
            'difficulty': 5,
            'teacher_notes': 'Проверено учителем',
            'is_verified': True,
        })
        self._import(payload)

        task = Task.objects.get(pk=task_id)
        self.assertEqual(task.text, 'Обновлённое условие')
        self.assertEqual(task.answer, 'Новый ответ')
        self.assertEqual(task.difficulty, 5)
        self.assertEqual(task.teacher_notes, 'Проверено учителем')
        self.assertTrue(task.is_verified)

    def test_dry_run_accepts_group_role_objects(self):
        output = []
        payload = self._task_payload(
            task_id='550e8400-e29b-41d4-a716-446655440001',
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )

        context = TaskImporter(
            mode='update',
            dry_run=True,
            create_missing=True,
            output=output.append,
        ).import_tasks_from_json(payload)

        self.assertIn('🔍 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР (--dry-run)', output)
        self.assertEqual(context.preview_summary['file_counts']['tasks'], 1)
        self.assertEqual(context.preview_summary['file_counts']['groups'], 1)
        self.assertEqual(context.preview_summary['task_uuid_counts']['new'], 1)
        self.assertEqual(
            context.preview_summary['dependency_counts'],
            {
                'missing_topics': 1,
                'missing_groups': 0,
                'broken_references': 0,
                'missing_classifications': 0,
            },
        )

    def test_dry_run_reports_missing_classification_references(self):
        payload = self._task_payload(
            task_id='550e8400-e29b-41d4-a716-446655440001',
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        payload['tasks'][0]['codifier_content_entries'] = [{
            'subject': 'Физика',
            'exam_type': 'oge',
            'year': 2099,
            'code': 'missing',
        }]

        context = TaskImporter(
            mode='update',
            dry_run=True,
            create_missing=True,
            output=lambda _message: None,
        ).import_tasks_from_json(payload)

        self.assertEqual(
            context.preview_summary['dependency_counts'][
                'missing_classifications'
            ],
            1,
        )

    def test_imports_base64_task_image_through_image_component(self):
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(
            task_id=task_id,
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        image_id = '990e8400-e29b-41d4-a716-446655440001'
        payload['task_images'] = [{
            'id': image_id,
            'task_id': task_id,
            'filename': 'diagram.bin',
            'base64_data': base64.b64encode(b'image-bytes').decode('ascii'),
            'caption': 'Схема опыта',
            'position': 'bottom_70',
        }]

        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            self._import(payload)
            image = TaskImage.objects.get(pk=image_id)
            self.assertEqual(image.position, 'bottom_70')
            self.assertEqual(image.caption, 'Схема опыта')
            with image.image.open('rb') as imported_file:
                self.assertEqual(imported_file.read(), b'image-bytes')

    def test_invalid_image_update_keeps_existing_file_and_metadata(self):
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(
            task_id=task_id,
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        image_id = '990e8400-e29b-41d4-a716-446655440001'
        payload['task_images'] = [{
            'id': image_id,
            'task_id': task_id,
            'filename': 'diagram.bin',
            'base64_data': base64.b64encode(b'original').decode('ascii'),
            'caption': 'Исходная подпись',
        }]

        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            self._import(payload)
            payload['task_images'][0]['base64_data'] = 'not-base64'
            payload['task_images'][0]['caption'] = 'Не сохранять'
            self._import(payload)

            image = TaskImage.objects.get(pk=image_id)
            self.assertEqual(image.caption, 'Исходная подпись')
            with image.image.open('rb') as imported_file:
                self.assertEqual(imported_file.read(), b'original')

    def test_catalog_source_is_resolved_and_updated_for_task(self):
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        source_id = '880e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(
            task_id=task_id,
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        payload['sources'] = [{
            'id': source_id,
            'name': 'Сборник задач по физике',
            'short_name': 'Сборник-9',
            'source_type': 'problem_book',
            'author': 'Первый автор',
        }]
        payload['tasks'][0]['source'] = {
            'id': source_id,
            'name': 'Сборник задач по физике',
            'short_name': 'Сборник-9',
        }

        self._import(payload)

        task = Task.objects.select_related('source').get(pk=task_id)
        self.assertEqual(str(task.source.pk), source_id)
        self.assertEqual(task.source.short_name, 'Сборник-9')
        self.assertEqual(task.source.author, 'Первый автор')

        payload['sources'][0]['name'] = 'Исправленное название'
        payload['sources'][0]['author'] = 'Новый автор'
        payload['tasks'][0]['source']['name'] = 'Исправленное название'
        self._import(payload)
        task.source.refresh_from_db()
        self.assertEqual(Source.objects.count(), 1)
        self.assertEqual(task.source.name, 'Исправленное название')
        self.assertEqual(task.source.author, 'Новый автор')

    def test_source_import_does_not_merge_distinct_uuids_by_isbn(self):
        existing = Source.objects.create(
            name='Физика. Первое название',
            isbn='978-5-00000-001-1',
        )
        payload = self._task_payload(
            task_id='550e8400-e29b-41d4-a716-446655440001',
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        payload['sources'] = [{
            'id': '880e8400-e29b-41d4-a716-446655440002',
            'name': 'Физика. Название с исправлением',
            'isbn': existing.isbn,
        }]
        payload['tasks'][0]['source'] = payload['sources'][0]

        self._import(payload)

        task = Task.objects.select_related('source').get()
        self.assertEqual(Source.objects.count(), 2)
        self.assertNotEqual(task.source_id, existing.pk)
        self.assertEqual(
            str(task.source_id),
            '880e8400-e29b-41d4-a716-446655440002',
        )

    def test_subtopic_is_created_once_and_bound_to_task_topic(self):
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        payload = self._task_payload(
            task_id=task_id,
            group_id='770e8400-e29b-41d4-a716-446655440001',
        )
        payload['tasks'][0]['subtopic'] = {
            'name': 'Второй закон Ньютона',
            'description': 'Связь силы и ускорения',
            'order': 2,
        }

        self._import(payload)
        self._import(payload)

        task = Task.objects.select_related('topic', 'subtopic').get(pk=task_id)
        self.assertEqual(task.subtopic.name, 'Второй закон Ньютона')
        self.assertEqual(task.subtopic.topic_id, task.topic_id)
        self.assertEqual(task.topic.subtopics.count(), 1)

    @staticmethod
    def _import(payload):
        return TaskImporter(
            mode='update',
            create_missing=True,
            output=lambda _message: None,
        ).import_tasks_from_json(payload)

    @staticmethod
    def _task_payload(*, task_id, group_id):
        return {
            'analog_groups': [{
                'id': group_id,
                'name': 'Группа для демонстрации',
                'difficulty': 3,
            }],
            'topics': [{
                'name': 'Динамика',
                'subject': 'Физика',
                'grade_level': 9,
                'section': 'Механика',
            }],
            'tasks': [{
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
                'groups': [{
                    'id': group_id,
                    'bank_role': 'demo',
                }],
            }],
        }
