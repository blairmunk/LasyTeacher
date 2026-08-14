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
            'актуальном формате 1.4' in warning
            for warning in data.warnings
        ))

    def test_validates_tasks_groups_and_summary(self):
        group_id = '770e8400-e29b-41d4-a716-446655440001'
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={
                    'tasks': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440001',
                            'text': 'Задача',
                            'answer': 'Ответ',
                            'topic': {'name': 'Тема'},
                            'groups': [group_id],
                        },
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440002',
                            'text': '',
                        },
                    ],
                    'analog_groups': [{'id': group_id, 'name': 'Группа'}],
                    'topics': [{'name': 'Тема'}],
                    'task_images': [{'id': 'image'}],
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

    def test_validates_source_uuid_and_warns_for_legacy_source(self):
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
            'Источник #2: отсутствует id' in warning
            for warning in data.warnings
        ))

    def test_warns_about_missing_group_reference(self):
        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(
                data={
                    'tasks': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440001',
                            'text': 'Задача',
                            'answer': 'Ответ',
                            'topic': {'name': 'Тема'},
                            'groups': ['770e8400-e29b-41d4-a716-446655440001'],
                        },
                    ],
                    'analog_groups': [],
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

    def test_warns_that_legacy_classification_does_not_create_relation(self):
        task = {
            'id': '550e8400-e29b-41d4-a716-446655440001',
            'text': 'Задача',
            'content_element': '1.1',
            'requirement_element': '2.1',
        }

        data = self.use_case.execute(
            ValidateTaskImportJsonRequest(data={'tasks': [task]}),
        )

        self.assertTrue(data.is_valid)
        self.assertTrue(any(
            'legacy-поля' in warning
            for warning in data.warnings
        ))
