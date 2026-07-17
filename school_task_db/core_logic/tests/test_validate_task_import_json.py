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
            },
        )

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
