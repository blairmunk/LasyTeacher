from unittest import TestCase

from core_logic.entities.task_import import TaskImportRequest, TaskImportResult
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase


class FakeTaskImportService:
    def __init__(self):
        self.request = None

    def execute_import(self, request):
        self.request = request
        return TaskImportResult(status='success', log_id='log-1')


class ExecuteTaskImportUseCaseTests(TestCase):
    def test_execute_delegates_to_import_service(self):
        service = FakeTaskImportService()
        request = TaskImportRequest(
            data={'tasks': []},
            filename='tasks.json',
            file_size=100,
            mode='update',
            dry_run=False,
            create_missing=True,
        )
        use_case = ExecuteTaskImportUseCase(task_import_service=service)

        result = use_case.execute(request)

        self.assertEqual(service.request, request)
        self.assertEqual(result.log_id, 'log-1')

    def test_execute_rejects_unknown_version_before_import_service(self):
        service = FakeTaskImportService()
        request = TaskImportRequest(
            data={'version': '9.0', 'tasks': []},
            filename='tasks.json',
            file_size=100,
        )

        result = ExecuteTaskImportUseCase(service).execute(request)

        self.assertFalse(result.success)
        self.assertIn('Неподдерживаемая версия', result.error)
        self.assertIsNone(service.request)

    def test_execute_rejects_invalid_classification_before_import_service(self):
        service = FakeTaskImportService()
        request = TaskImportRequest(
            data={
                'version': '1.4',
                'tasks': [{
                    'id': '550e8400-e29b-41d4-a716-446655440001',
                    'text': 'Задание',
                    'codifier_content_entries': [{
                        'subject': 'Физика',
                        'exam_type': 'oge',
                        'code': '1.1',
                    }],
                }],
            },
            filename='tasks.json',
            file_size=100,
        )

        result = ExecuteTaskImportUseCase(service).execute(request)

        self.assertFalse(result.success)
        self.assertIn('не содержит year', result.error)
        self.assertIsNone(service.request)
