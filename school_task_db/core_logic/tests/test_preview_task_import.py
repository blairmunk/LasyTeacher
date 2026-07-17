from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportPreviewResult,
)
from core_logic.use_cases.preview_task_import import PreviewTaskImportUseCase


class FakeTaskImportService:
    def __init__(self):
        self.request = None

    def preview_import(self, request):
        self.request = request
        return TaskImportPreviewResult(preview={'tasks_in_context': 0})


class PreviewTaskImportUseCaseTests(TestCase):
    def test_execute_delegates_to_import_service(self):
        service = FakeTaskImportService()
        request = TaskImportPreviewRequest(data={'tasks': []})
        use_case = PreviewTaskImportUseCase(task_import_service=service)

        result = use_case.execute(request)

        self.assertEqual(service.request, request)
        self.assertEqual(result.preview, {'tasks_in_context': 0})
