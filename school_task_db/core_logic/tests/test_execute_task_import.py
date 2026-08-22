from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase


class FakeTaskImportRunner:
    def __init__(self, summary=None, error=None):
        self.summary = summary or TaskImportRunSummary()
        self.error = error
        self.request = None

    def execute_import(self, request):
        self.request = request
        if self.error:
            raise self.error
        return self.summary


class FakeTaskImportLogRepository:
    def __init__(self):
        self.started = []
        self.completed = []
        self.failed = []

    def start(self, request):
        self.started.append(request)
        return 'log-1'

    def complete(self, log_id, summary, duration_ms):
        self.completed.append((log_id, summary, duration_ms))

    def fail(self, log_id, error, duration_ms):
        self.failed.append((log_id, error, duration_ms))


class ExecuteTaskImportUseCaseTests(TestCase):
    def test_executes_and_journals_normalized_summary(self):
        summary = TaskImportRunSummary(
            created_by_type={'tasks': 2, 'topics': 1},
            context_counts={'tasks': 2, 'topics': 1, 'subtopics': 0},
        )
        runner = FakeTaskImportRunner(summary=summary)
        log_repo = FakeTaskImportLogRepository()
        clock_values = iter((10.0, 10.25))
        request = self._request()
        use_case = ExecuteTaskImportUseCase(
            task_import_runner=runner,
            task_import_log_repo=log_repo,
            clock=lambda: next(clock_values),
        )

        result = use_case.execute(request)

        self.assertEqual(runner.request, request)
        self.assertEqual(log_repo.started, [request])
        self.assertEqual(len(log_repo.completed), 1)
        completed_log_id, completed_summary, completed_duration = (
            log_repo.completed[0]
        )
        self.assertEqual(completed_log_id, 'log-1')
        self.assertEqual(completed_duration, 250)
        self.assertEqual(completed_summary.created_by_type, summary.created_by_type)
        self.assertEqual(completed_summary.warnings, 1)
        self.assertEqual(
            completed_summary.warning_messages,
            ('Массив "tasks" пуст',),
        )
        self.assertEqual(log_repo.failed, [])
        self.assertEqual(result.log_id, 'log-1')
        self.assertEqual(result.duration_ms, 250)
        self.assertEqual(result.stats['created'], 2)
        self.assertEqual(result.stats['warnings'], 1)
        self.assertIn('Предупреждений: 1', result.message)
        self.assertIn('Массив "tasks" пуст', result.message)
        self.assertIn('Файл: tasks.json (100 Б)', result.message)

    def test_merges_runtime_and_validation_warnings_without_partial_status(self):
        runner = FakeTaskImportRunner(summary=TaskImportRunSummary(
            warnings=1,
            warning_messages=('Предупреждение runtime',),
        ))
        log_repo = FakeTaskImportLogRepository()

        result = ExecuteTaskImportUseCase(
            task_import_runner=runner,
            task_import_log_repo=log_repo,
        ).execute(self._request(data={
            'format_version': '1.2',
            'tasks': [],
        }))

        summary = log_repo.completed[0][1]
        self.assertTrue(result.success)
        self.assertEqual(summary.status, 'success')
        self.assertEqual(summary.warnings, 3)
        self.assertEqual(summary.warning_messages[0], 'Предупреждение runtime')
        self.assertTrue(any(
            'формате 1.5' in warning
            for warning in summary.warning_messages
        ))
        self.assertIn('Массив "tasks" пуст', summary.warning_messages)

    def test_records_runner_failure(self):
        runner = FakeTaskImportRunner(error=ValueError('Ошибка импортера'))
        log_repo = FakeTaskImportLogRepository()
        clock_values = iter((3.0, 3.01))
        use_case = ExecuteTaskImportUseCase(
            task_import_runner=runner,
            task_import_log_repo=log_repo,
            clock=lambda: next(clock_values),
        )

        result = use_case.execute(self._request())

        self.assertFalse(result.success)
        self.assertEqual(result.log_id, 'log-1')
        self.assertEqual(result.error, 'Ошибка импортера')
        self.assertEqual(log_repo.completed, [])
        self.assertEqual(
            log_repo.failed,
            [('log-1', 'Ошибка импортера', 9)],
        )

    def test_rejects_unknown_version_before_runner_and_log(self):
        runner = FakeTaskImportRunner()
        log_repo = FakeTaskImportLogRepository()
        request = self._request(data={'version': '9.0', 'tasks': []})

        result = ExecuteTaskImportUseCase(
            runner,
            log_repo,
        ).execute(request)

        self.assertFalse(result.success)
        self.assertIn('Неподдерживаемая версия', result.error)
        self.assertIsNone(runner.request)
        self.assertEqual(log_repo.started, [])

    def test_rejects_invalid_classification_before_runner_and_log(self):
        runner = FakeTaskImportRunner()
        log_repo = FakeTaskImportLogRepository()
        request = self._request(data={
            'version': '1.5',
            'tasks': [{
                'id': '550e8400-e29b-41d4-a716-446655440001',
                'text': 'Задание',
                'codifier_content_entries': [{
                    'subject': 'Физика',
                    'exam_type': 'oge',
                    'code': '1.1',
                }],
            }],
        })

        result = ExecuteTaskImportUseCase(
            runner,
            log_repo,
        ).execute(request)

        self.assertFalse(result.success)
        self.assertIn('не содержит year', result.error)
        self.assertIsNone(runner.request)
        self.assertEqual(log_repo.started, [])

    @staticmethod
    def _request(data=None):
        return TaskImportRequest(
            data=data or {'tasks': []},
            filename='tasks.json',
            file_size=100,
            mode='update',
            dry_run=False,
            create_missing=True,
        )
