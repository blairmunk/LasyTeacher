from contextlib import contextmanager
from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.use_cases.apply_task_import import ApplyTaskImportUseCase


class FakeTaskImportWriteSession:
    def __init__(self):
        self.calls = []
        self.result = TaskImportRunSummary(created_by_type={'tasks': 1})

    def import_sources(self, records):
        self.calls.append(('sources', records))

    def import_groups(self, records):
        self.calls.append(('groups', records))

    def import_topics(self, records):
        self.calls.append(('topics', records))

    def import_tasks(self, records):
        self.calls.append(('tasks', records))

    def import_task_group_relations(self, records):
        self.calls.append(('relations', records))

    def import_images(self, records):
        self.calls.append(('images', records))

    def summary(self):
        self.calls.append(('summary', None))
        return self.result


class FakeTransactionManager:
    def __init__(self):
        self.entered = 0

    @contextmanager
    def atomic(self):
        self.entered += 1
        yield


class ApplyTaskImportUseCaseTests(TestCase):
    def test_applies_all_stages_in_dependency_order_inside_transaction(self):
        session = FakeTaskImportWriteSession()
        transaction_manager = FakeTransactionManager()
        data = {
            'sources': [{'id': 'source'}],
            'analog_groups': [{'id': 'group'}],
            'topics': [{'id': 'topic'}],
            'tasks': [{'id': 'task'}],
            'task_images': [{'id': 'image'}],
        }

        result = ApplyTaskImportUseCase(
            session,
            transaction_manager,
        ).execute(self._request(data))

        self.assertIs(result, session.result)
        self.assertEqual(transaction_manager.entered, 1)
        self.assertEqual(
            [name for name, _records in session.calls],
            [
                'sources',
                'groups',
                'topics',
                'tasks',
                'relations',
                'images',
                'summary',
            ],
        )

    def test_skips_topic_creation_but_still_links_imported_tasks(self):
        session = FakeTaskImportWriteSession()
        data = {
            'topics': [{'id': 'topic'}],
            'tasks': [{'id': 'task'}],
        }

        ApplyTaskImportUseCase(
            session,
            FakeTransactionManager(),
        ).execute(self._request(data, create_missing=False))

        self.assertEqual(
            [name for name, _records in session.calls],
            ['tasks', 'relations', 'summary'],
        )
        self.assertIs(session.calls[1][1], data['tasks'])

    def test_rejects_invalid_mode_before_opening_transaction(self):
        session = FakeTaskImportWriteSession()
        transaction_manager = FakeTransactionManager()

        with self.assertRaisesRegex(ValueError, 'Неверный режим'):
            ApplyTaskImportUseCase(
                session,
                transaction_manager,
            ).execute(self._request({}, mode='unknown'))

        self.assertEqual(transaction_manager.entered, 0)
        self.assertEqual(session.calls, [])

    @staticmethod
    def _request(data, *, mode='update', create_missing=True):
        return TaskImportRequest(
            data=data,
            filename='tasks.json',
            file_size=0,
            mode=mode,
            create_missing=create_missing,
        )
