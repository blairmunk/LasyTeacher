from unittest import TestCase

from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonRequest,
    ValidateTaskImportJsonUseCase,
)


class ValidateTaskImportJsonUseCaseTests(TestCase):
    def setUp(self):
        self.use_case = ValidateTaskImportJsonUseCase()

    def test_rejects_non_object_root(self):
        data = self.use_case.execute(ValidateTaskImportJsonRequest(data=[]))

        self.assertFalse(data.is_valid)
        self.assertEqual(data.errors, ['Корневой элемент должен быть объектом {}'])

    def test_rejects_missing_tasks_field(self):
        data = self.use_case.execute(ValidateTaskImportJsonRequest(data={}))

        self.assertFalse(data.is_valid)
        self.assertEqual(data.errors, ['Отсутствует обязательное поле "tasks"'])

    def test_rejects_non_list_tasks_field(self):
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(data={'tasks': {}}),
        )

        self.assertFalse(data.is_valid)
        self.assertEqual(data.errors, ['"tasks" должен быть массивом'])

    def test_rejects_unknown_transfer_format_version(self):
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={'version': '9.0', 'tasks': []},
            ),
        )

        self.assertFalse(data.is_valid)
        self.assertIn('Неподдерживаемая версия', data.errors[0])

    def test_accepts_old_version_with_migration_warning(self):
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={'format_version': '1.2', 'tasks': []},
            ),
        )

        self.assertTrue(data.is_valid)
        self.assertTrue(any(
            'актуальном формате 1.5' in warning
            for warning in data.warnings
        ))

    def test_validates_tasks_groups_and_summary(self):
        group_id = '770e8400-e29b-41d4-a716-446655440001'
        topic_id = '660e8400-e29b-41d4-a716-446655440001'
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={
                    'tasks': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440001',
                            'text': 'Задача',
                            'answer': 'Ответ',
                            'topic': {'id': topic_id},
                            'groups': [group_id],
                        },
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440002',
                            'text': '',
                        },
                    ],
                    'analog_groups': [{'id': group_id, 'name': 'Группа'}],
                    'topics': [{
                        'id': topic_id,
                        'name': 'Тема',
                        'subject': 'Физика',
                        'grade_level': 9,
                    }],
                    'task_images': [{
                        'id': '990e8400-e29b-41d4-a716-446655440001',
                        'task_id': '550e8400-e29b-41d4-a716-446655440001',
                        'base64_data': 'aW1hZ2U=',
                    }],
                    'sources': [{
                        'id': '880e8400-e29b-41d4-a716-446655440001',
                        'name': 'Сборник',
                    }],
                },
            ),
        )

        self.assertFalse(data.is_valid)
        self.assertEqual(data.errors, ['Задание #2: отсутствует text'])
        self.assertIn('Задание #2: нет ответа', data.warnings)
        self.assertIn('Задание #2: нет темы', data.warnings)
        self.assertEqual(
            data.summary,
            {
                'tasks_total': 2,
                'tasks_valid': 1,
                'tasks_errors': 1,
                'groups_total': 1,
                'topics_total': 1,
                'images_total': 1,
                'sources_total': 1,
            },
        )

    def test_requires_valid_source_uuid(self):
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={
                    'tasks': [],
                    'sources': [
                        {'id': 'not-a-uuid', 'name': 'Некорректный'},
                        {'name': 'Старый формат'},
                    ],
                },
            ),
        )

        self.assertFalse(data.is_valid)
        self.assertIn('Источник #1: некорректный UUID', data.errors[0])
        self.assertTrue(any(
            'Источник #2: отсутствует id' in error
            for error in data.errors
        ))

    def test_rejects_task_uuid_duplicates_that_differ_only_by_case(self):
        task_id = '550e8400-e29b-41d4-a716-4466554400ab'

        data = self.use_case.execute(ValidateTaskImportJsonRequest(data={
            'tasks': [
                {'id': task_id, 'text': 'Первое'},
                {'id': task_id.upper(), 'text': 'Второе'},
            ],
        }))

        self.assertFalse(data.is_valid)
        self.assertTrue(any(
            'Задание #2: дублирующийся id' in error
            for error in data.errors
        ))

    def test_requires_uuid_object_for_task_source_reference(self):
        task = {
            'id': '550e8400-e29b-41d4-a716-446655440001',
            'text': 'Задача',
            'source': 'Сборник по имени',
        }

        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(data={'tasks': [task]}),
        )

        self.assertFalse(data.is_valid)
        self.assertTrue(any(
            'source должен быть объектом с id' in error
            for error in data.errors
        ))

    def test_rejects_image_for_task_missing_from_same_file(self):
        data = self.use_case.execute(ValidateTaskImportJsonRequest(data={
            'tasks': [],
            'task_images': [{
                'id': '990e8400-e29b-41d4-a716-446655440001',
                'task_id': '550e8400-e29b-41d4-a716-446655440001',
                'base64_data': 'aW1hZ2U=',
            }],
        }))

        self.assertFalse(data.is_valid)
        self.assertTrue(any(
            'не найден среди tasks этого файла' in error
            for error in data.errors
        ))

    def test_warns_about_missing_group_reference(self):
        topic_id = '660e8400-e29b-41d4-a716-446655440001'
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={
                    'tasks': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440001',
                            'text': 'Задача',
                            'answer': 'Ответ',
                            'topic': {'id': topic_id},
                            'groups': ['770e8400-e29b-41d4-a716-446655440001'],
                        },
                    ],
                    'analog_groups': [],
                    'topics': [{
                        'id': topic_id,
                        'name': 'Тема',
                        'subject': 'Физика',
                        'grade_level': 9,
                    }],
                },
            ),
        )

        self.assertTrue(data.is_valid)
        self.assertEqual(
            data.warnings,
            [
                'Задание #1: ссылка на группу 55440001... '
                'не найдена в analog_groups (будет искать в БД)',
            ],
        )

    def test_rejects_group_name_and_invalid_group_uuid(self):
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={
                    'tasks': [{
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'text': 'Задача',
                        'group_name': 'Группа по имени',
                    }],
                    'analog_groups': [{
                        'id': 'not-a-uuid',
                        'name': 'Группа',
                    }],
                },
            ),
        )

        self.assertFalse(data.is_valid)
        self.assertTrue(any(
            'legacy-поле group_name' in error
            for error in data.errors
        ))
        self.assertTrue(any(
            'Группа #1: некорректный UUID' in error
            for error in data.errors
        ))

    def test_accepts_group_reference_with_bank_role(self):
        group_id = '770e8400-e29b-41d4-a716-446655440001'

        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={
                    'tasks': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440001',
                            'text': 'Демонстрационная задача',
                            'groups': [
                                {
                                    'id': group_id,
                                    'bank_role': 'demo',
                                },
                            ],
                        },
                    ],
                    'analog_groups': [
                        {'id': group_id, 'name': 'Динамика'},
                    ],
                },
            ),
        )

        self.assertTrue(data.is_valid)
        self.assertEqual(data.errors, [])

    def test_rejects_unsupported_group_bank_role(self):
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={
                    'tasks': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440001',
                            'text': 'Задача',
                            'groups': [
                                {
                                    'id': '770e8400-e29b-41d4-a716-446655440001',
                                    'bank_role': 'unknown',
                                },
                            ],
                        },
                    ],
                    'analog_groups': [],
                },
            ),
        )

        self.assertFalse(data.is_valid)
        self.assertIn('Unsupported specific task bank role', data.errors[0])

    def test_validates_portable_codifier_references(self):
        task = {
            'id': '550e8400-e29b-41d4-a716-446655440001',
            'text': 'Задача',
            'codifier_content_entries': [{
                'subject': 'Физика',
                'exam_type': 'oge',
                'year': 2026,
                'code': '1.1',
            }],
            'codifier_requirements': [{
                'subject': 'Физика',
                'exam_type': 'oge',
                'code': '2.1',
            }],
        }

        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(data={'tasks': [task]}),
        )

        self.assertFalse(data.is_valid)
        self.assertIn(
            'codifier_requirements[1] не содержит year',
            data.errors[0],
        )

    def test_rejects_non_array_codifier_references(self):
        task = {
            'id': '550e8400-e29b-41d4-a716-446655440001',
            'text': 'Задача',
            'codifier_content_entries': {},
        }

        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(data={'tasks': [task]}),
        )

        self.assertFalse(data.is_valid)
        self.assertIn('должен быть массивом', data.errors[0])

    def test_rejects_removed_legacy_classification_fields(self):
        task = {
            'id': '550e8400-e29b-41d4-a716-446655440001',
            'text': 'Задача',
            'content_element': '1.1',
            'requirement_element': '2.1',
        }

        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(data={'tasks': [task]}),
        )

        self.assertFalse(data.is_valid)
        self.assertTrue(any(
            'legacy-поля' in error
            for error in data.errors
        ))

    def test_requires_uuid_catalog_and_references_for_topics(self):
        task_id = '550e8400-e29b-41d4-a716-446655440001'
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(data={
                'version': '1.5',
                'topics': [{
                    'name': 'Динамика',
                    'subject': 'Физика',
                    'grade_level': 9,
                }],
                'tasks': [{
                    'id': task_id,
                    'text': 'Задача',
                    'topic': {'name': 'Динамика'},
                    'subtopic': 'Второй закон Ньютона',
                }],
            }),
        )

        self.assertFalse(data.is_valid)
        self.assertTrue(any(
            'Тема #1: отсутствует id' in error
            for error in data.errors
        ))
        self.assertTrue(any(
            'topic: отсутствует id' in error
            for error in data.errors
        ))
        self.assertTrue(any(
            'subtopic должен быть объектом с id' in error
            for error in data.errors
        ))

    def test_validates_nested_subtopic_parent(self):
        topic_id = '660e8400-e29b-41d4-a716-446655440001'
        other_topic_id = '660e8400-e29b-41d4-a716-446655440002'
        subtopic_id = '661e8400-e29b-41d4-a716-446655440001'
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(data={
                'version': '1.5',
                'topics': [{
                    'id': topic_id,
                    'name': 'Динамика',
                    'subject': 'Физика',
                    'grade_level': 9,
                    'subtopics': [{
                        'id': subtopic_id,
                        'name': 'Второй закон Ньютона',
                    }],
                }, {
                    'id': other_topic_id,
                    'name': 'Кинематика',
                    'subject': 'Физика',
                    'grade_level': 9,
                }],
                'tasks': [{
                    'id': '550e8400-e29b-41d4-a716-446655440001',
                    'text': 'Задача',
                    'topic': {'id': other_topic_id},
                    'subtopic': {'id': subtopic_id},
                }],
            }),
        )

        self.assertFalse(data.is_valid)
        self.assertTrue(any(
            'принадлежит другой теме' in error
            for error in data.errors
        ))
