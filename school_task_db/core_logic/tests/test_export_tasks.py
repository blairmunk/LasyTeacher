from unittest import TestCase

from core_logic.entities.task import (
    TaskExportFilters,
    TaskExportGroupRef,
    TaskExportSourceRef,
    TaskExportTaskSource,
    TaskExportTopicRef,
)
from core_logic.use_cases.export_tasks import ExportTasksRequest, ExportTasksUseCase


class FakeTaskRepository:
    def __init__(self):
        self.filters = None
        topic = TaskExportTopicRef('Динамика', 'Физика', 9)
        source = TaskExportSourceRef(pk='source-1', name='Сборник')
        groups = (
            TaskExportGroupRef(
                pk='group-1',
                name='Группа',
                bank_role='demo',
            ),
        )
        self.sources = [
            TaskExportTaskSource(
                pk='task-1',
                text='Задание 1',
                topic=topic,
                source=source,
                groups=groups,
            ),
            TaskExportTaskSource(
                pk='task-2',
                text='Задание 2',
                topic=topic,
                source=source,
                groups=groups,
            ),
        ]

    def get_task_export_sources(self, filters):
        self.filters = filters
        return self.sources


class ExportTasksUseCaseTests(TestCase):
    def test_execute_delegates_payload_building_to_repository(self):
        repo = FakeTaskRepository()
        filters = TaskExportFilters(topic_id='topic-1', subject='Физика', grade='9')
        use_case = ExportTasksUseCase(task_repo=repo)

        data = use_case.execute(
            ExportTasksRequest(filters=filters, export_date='2026-07-17'),
        )

        self.assertEqual(repo.filters, filters)
        self.assertEqual(data.payload['version'], '1.2')
        self.assertEqual(data.payload['export_date'], '2026-07-17')
        self.assertEqual(data.payload['tasks'][0]['id'], 'task-1')
        self.assertEqual(
            data.payload['tasks'][0]['groups'],
            [{'id': 'group-1', 'bank_role': 'demo'}],
        )
        self.assertEqual(len(data.payload['tasks']), 2)
        self.assertEqual(len(data.payload['topics']), 1)
        self.assertEqual(len(data.payload['sources']), 1)
        self.assertEqual(len(data.payload['analog_groups']), 1)
