from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportExecutionSubmissionRequest,
    TaskImportExecutionSubmissionResult,
    TaskImportRequest,
    TaskImportResult,
)
from core_logic.use_cases.execute_task_import_submission import (
    ExecuteTaskImportSubmissionUseCase,
)


class FakePrepareSubmissionUseCase:
    def __init__(self, result):
        self.result = result
        self.request = None

    def execute(self, request):
        self.request = request
        return self.result


class FakeExecuteImportUseCase:
    def __init__(self):
        self.request = None

    def execute(self, request):
        self.request = request
        return TaskImportResult(status='success', log_id='log-1')


class ExecuteTaskImportSubmissionUseCaseTests(TestCase):
    def test_returns_error_when_submission_is_invalid(self):
        submission_request = self._submission_request()
        prepare_use_case = FakePrepareSubmissionUseCase(
            TaskImportExecutionSubmissionResult(error='Невалидный JSON'),
        )
        execute_use_case = FakeExecuteImportUseCase()
        use_case = ExecuteTaskImportSubmissionUseCase(
            task_import_service=None,
            prepare_submission_use_case=prepare_use_case,
            execute_import_use_case=execute_use_case,
        )

        result = use_case.execute(submission_request)

        self.assertEqual(prepare_use_case.request, submission_request)
        self.assertEqual(result.status, 'error')
        self.assertEqual(result.error, 'Невалидный JSON')
        self.assertIsNone(execute_use_case.request)

    def test_executes_prepared_import_request(self):
        import_request = TaskImportRequest(
            data={'tasks': []},
            filename='tasks.json',
            file_size=100,
        )
        prepare_use_case = FakePrepareSubmissionUseCase(
            TaskImportExecutionSubmissionResult(
                import_request=import_request,
            ),
        )
        execute_use_case = FakeExecuteImportUseCase()
        use_case = ExecuteTaskImportSubmissionUseCase(
            task_import_service=None,
            prepare_submission_use_case=prepare_use_case,
            execute_import_use_case=execute_use_case,
        )

        result = use_case.execute(self._submission_request())

        self.assertEqual(result.status, 'success')
        self.assertEqual(result.log_id, 'log-1')
        self.assertEqual(execute_use_case.request, import_request)

    def _submission_request(self):
        return TaskImportExecutionSubmissionRequest(
            filename='tasks.json',
            file_size=2,
            content=b'{}',
            form_data={},
        )
