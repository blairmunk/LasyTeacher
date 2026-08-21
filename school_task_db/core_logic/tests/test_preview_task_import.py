from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportRunSummary,
)
from core_logic.use_cases.preview_task_import import PreviewTaskImportUseCase


class FakeTaskImportRunner:
    def __init__(self, error=None):
        self.error = error
        self.request = None

    def preview_import(self, request):
        self.request = request
        if self.error:
            raise self.error
        return TaskImportRunSummary(preview={'tasks_in_context': 0})


class PreviewTaskImportUseCaseTests(TestCase):
    def test_returns_runner_preview(self):
        runner = FakeTaskImportRunner()
        request = TaskImportPreviewRequest(data={'tasks': []})
        use_case = PreviewTaskImportUseCase(task_import_runner=runner)

        result = use_case.execute(request)

        self.assertEqual(runner.request, request)
        self.assertEqual(result.preview, {'tasks_in_context': 0})

    def test_converts_runner_failure_to_warning(self):
        runner = FakeTaskImportRunner(error=ValueError('Недоступна БД'))

        result = PreviewTaskImportUseCase(runner).execute(
            TaskImportPreviewRequest(data={'tasks': []}),
        )

        self.assertFalse(result.success)
        self.assertEqual(result.warning, 'Ошибка dry-run: Недоступна БД')
