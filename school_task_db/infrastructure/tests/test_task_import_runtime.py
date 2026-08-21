from types import SimpleNamespace

from django.test import SimpleTestCase

from infrastructure.importers.runtime import (
    TaskImportRegistry,
    TaskImportRuntime,
    TaskImportStatistics,
)


class TaskImportRegistryTests(SimpleTestCase):
    def test_tracks_transaction_objects_by_explicit_role(self):
        registry = TaskImportRegistry()
        task = object()
        topic = object()

        registry.remember_task('task-1', task)
        registry.remember_topic('topic-1', topic)

        self.assertIs(registry.task('task-1'), task)
        self.assertIs(registry.topic('topic-1'), topic)
        self.assertIsNone(registry.group('missing'))
        self.assertEqual(
            registry.counts(),
            {
                'topics': 1,
                'subtopics': 0,
                'groups': 0,
                'sources': 0,
                'tasks': 1,
            },
        )


class TaskImportStatisticsTests(SimpleTestCase):
    def test_deduplicates_same_object_operation(self):
        stats = TaskImportStatistics()

        stats.record_created('tasks', 'task-1')
        stats.record_created('tasks', 'task-1')
        stats.record_created('tasks', 'task-2')
        stats.add_error('Ошибка задания', ValueError('bad'))

        self.assertEqual(stats.created_by_type, {'tasks': 2})
        self.assertEqual(len(stats.errors), 1)
        self.assertEqual(stats.errors[0].message, 'Ошибка задания')
        self.assertEqual(stats.errors[0].exception, 'bad')


class TaskImportRuntimeTests(SimpleTestCase):
    def test_skip_records_existing_object_without_creating(self):
        runtime = self._runtime(mode='skip')
        existing = SimpleNamespace(pk='task-1')

        action = runtime.object_action(
            existing,
            {'id': '550e8400-e29b-41d4-a716-446655440001'},
            'tasks',
        )

        self.assertEqual(action, 'skip')
        self.assertEqual(runtime.stats.skipped_by_type, {'tasks': 1})

    def test_strict_rejects_existing_object(self):
        runtime = self._runtime(mode='strict')

        with self.assertRaisesRegex(ValueError, 'strict режиме'):
            runtime.object_action(
                SimpleNamespace(pk='task-1'),
                {'id': '550e8400-e29b-41d4-a716-446655440001'},
                'tasks',
            )

    @staticmethod
    def _runtime(*, mode):
        return TaskImportRuntime(
            mode=mode,
            verbose=False,
            create_missing=True,
            output=lambda _message: None,
        )
