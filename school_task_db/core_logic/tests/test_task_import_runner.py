from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportPreviewFacts,
    TaskImportPreviewRequest,
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.services.task_import_runner import TaskImportRunnerService


class FakeWriteSession:
    def __init__(self):
        self.calls = []

    def import_sources(self, records):
        self.calls.append('sources')

    def import_groups(self, records):
        self.calls.append('groups')

    def import_topics(self, records):
        self.calls.append('topics')

    def import_tasks(self, records):
        self.calls.append('tasks')

    def import_task_group_relations(self, records):
        self.calls.append('relations')

    def import_images(self, records):
        self.calls.append('images')

    def summary(self):
        return TaskImportRunSummary(created_by_type={'tasks': 1})


class FakeWriteSessionFactory:
    def __init__(self):
        self.calls = []
        self.session = FakeWriteSession()

    def create(self, *, mode, create_missing):
        self.calls.append((mode, create_missing))
        return self.session


class FakePreviewRepository:
    def __init__(self):
        self.lookups = []

    def get_facts(self, lookup):
        self.lookups.append(lookup)
        return TaskImportPreviewFacts()


class FakeTransactionManager:
    class _Atomic:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def atomic(self):
        return self._Atomic()


class TaskImportRunnerServiceTests(TestCase):
    def test_execute_creates_fresh_write_session_for_request(self):
        factory = FakeWriteSessionFactory()
        runner = self._runner(factory)

        result = runner.execute_import(TaskImportRequest(
            data={'tasks': []},
            filename='tasks.json',
            file_size=0,
            mode='skip',
            create_missing=False,
        ))

        self.assertEqual(factory.calls, [('skip', False)])
        self.assertEqual(factory.session.calls, ['tasks', 'relations'])
        self.assertEqual(result.tasks_created, 1)

    def test_dry_run_does_not_create_write_session(self):
        factory = FakeWriteSessionFactory()
        preview_repo = FakePreviewRepository()
        runner = self._runner(factory, preview_repo=preview_repo)

        result = runner.execute_import(TaskImportRequest(
            data={'tasks': []},
            filename='tasks.json',
            file_size=0,
            dry_run=True,
        ))

        self.assertEqual(factory.calls, [])
        self.assertEqual(result.preview['file_counts']['tasks'], 0)
        self.assertEqual(len(preview_repo.lookups), 1)

    def test_explicit_preview_uses_same_read_only_path(self):
        factory = FakeWriteSessionFactory()
        preview_repo = FakePreviewRepository()
        runner = self._runner(factory, preview_repo=preview_repo)

        result = runner.preview_import(TaskImportPreviewRequest(
            data={'tasks': []},
        ))

        self.assertEqual(factory.calls, [])
        self.assertEqual(result.preview['file_counts']['tasks'], 0)
        self.assertEqual(len(preview_repo.lookups), 1)

    @staticmethod
    def _runner(factory, *, preview_repo=None):
        return TaskImportRunnerService(
            write_session_factory=factory,
            preview_repo=preview_repo or FakePreviewRepository(),
            transaction_manager=FakeTransactionManager(),
        )
