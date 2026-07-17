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
