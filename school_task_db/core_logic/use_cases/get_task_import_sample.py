"""Build sample task import JSON payload."""

from core_logic.entities.task_import import TaskImportSampleData
from core_logic.value_objects.task_transfer_format import (
    TASK_TRANSFER_FORMAT_VERSION,
)


class GetTaskImportSampleUseCase:
    def execute(self) -> TaskImportSampleData:
        return TaskImportSampleData(
            filename='sample_import.json',
            payload={
                'version': TASK_TRANSFER_FORMAT_VERSION,
                'description': (
                    'Пример файла для импорта заданий '
                    '(v1.4 — с UUID источников и явными связями '
                    'кодификаторов)'
                ),
                'sources': [
                    {
                        'id': '880e8400-e29b-41d4-a716-446655440001',
                        'name': 'Перышкин А.В. Физика. 8 класс',
                        'short_name': 'Перышкин-8',
                        'source_type': 'textbook',
                        'author': 'Перышкин А.В.',
                        'year': 2020,
                    },
                ],
                'analog_groups': [
                    {
                        'id': '770e8400-e29b-41d4-a716-446655440001',
                        'name': 'Линейные уравнения — базовый',
                        'description': (
                            'Простые линейные уравнения вида ax + b = c'
                        ),
                    },
                    {
                        'id': '770e8400-e29b-41d4-a716-446655440002',
                        'name': 'Сложение дробей',
                        'description': (
                            'Сложение обыкновенных дробей с разными '
                            'знаменателями'
                        ),
                    },
                ],
                'topics': [
                    {
                        'name': 'Линейные уравнения',
                        'subject': 'Математика',
                        'grade_level': 7,
                        'section': 'Алгебра',
                        'description': 'Решение линейных уравнений',
                    },
                ],
                'tasks': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'text': 'Решите уравнение: $2x + 5 = 15$',
                        'answer': '$x = 5$',
                        'short_solution': '$2x = 10$, $x = 5$',
                        'full_solution': (
                            'Перенесём 5 в правую часть:\n'
                            '$$2x = 15 - 5 = 10$$\n'
                            'Разделим на 2: $x = 5$'
                        ),
                        'hint': 'Перенесите число в правую часть',
                        'difficulty': 1,
                        'task_type': 'computational',
                        'cognitive_level': 'apply',
                        'grade': 7,
                        'year': 2024,
                        'is_verified': True,
                        'teacher_notes': (
                            'Базовое задание, дети справляются хорошо'
                        ),
                        'codifier_content_entries': [],
                        'codifier_requirements': [],
                        'source': {
                            'id': '880e8400-e29b-41d4-a716-446655440001',
                            'name': 'Перышкин А.В. Физика. 8 класс',
                            'short_name': 'Перышкин-8',
                        },
                        'source_detail': 'Стр. 45, №12',
                        'topic': {
                            'name': 'Линейные уравнения',
                            'subject': 'Математика',
                            'grade_level': 7,
                        },
                        'groups': [{
                            'id': '770e8400-e29b-41d4-a716-446655440001',
                            'bank_role': 'demo',
                        }],
                    },
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440002',
                        'text': (
                            'Найдите значение выражения: '
                            '$\\frac{3}{4} + \\frac{1}{6}$'
                        ),
                        'answer': '$\\frac{11}{12}$',
                        'short_solution': (
                            '$\\frac{9}{12} + \\frac{2}{12} = '
                            '\\frac{11}{12}$'
                        ),
                        'difficulty': 1,
                        'task_type': 'computational',
                        'cognitive_level': 'apply',
                        'grade': 6,
                        'is_verified': False,
                        'codifier_content_entries': [],
                        'codifier_requirements': [],
                        'topic': {
                            'name': 'Обыкновенные дроби',
                            'subject': 'Математика',
                            'grade_level': 6,
                        },
                        'groups': [{
                            'id': '770e8400-e29b-41d4-a716-446655440002',
                            'bank_role': 'control',
                        }],
                    },
                ],
                'task_images': [],
            },
        )
