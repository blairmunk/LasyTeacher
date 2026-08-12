from unittest import TestCase

from core_logic.entities.task import (
    TaskExportClassificationRef,
    TaskExportFilters,
    TaskExportGroupRef,
    TaskExportSourceRef,
    TaskExportTaskSource,
    TaskExportTopicRef,
)
from core_logic.use_cases.export_tasks import ExportTasksRequest, ExportTasksUseCase


class FakeTaskExportRepository:
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
                content_entries=(TaskExportClassificationRef(
                    subject='Физика',
                    exam_type='oge',
                    year=2026,
                    code='1.1',
                    name='Механика',
                    codifier_name='ОГЭ 2026',
                ),),
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
        repo = FakeTaskExportRepository()
        filters = TaskExportFilters(topic_id='topic-1', subject='Физика', grade='9')
        use_case = ExportTasksUseCase(task_export_repo=repo)

        data = use_case.execute(
            ExportTasksRequest(filters=filters, export_date='2026-07-17'),
        )

        self.assertEqual(repo.filters, filters)
        self.assertEqual(data.payload['version'], '1.4')
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
        self.assertEqual(
            data.payload['tasks'][0]['codifier_content_entries'][0],
            {
                'subject': 'Физика',
                'exam_type': 'oge',
                'year': 2026,
                'code': '1.1',
                'name': 'Механика',
                'codifier_name': 'ОГЭ 2026',
            },
        )
        self.assertNotIn('content_element', data.payload['tasks'][0])
        self.assertNotIn('requirement_element', data.payload['tasks'][0])

    def test_execute_can_omit_group_and_topic_catalogs(self):
        payload = ExportTasksUseCase(
            task_export_repo=FakeTaskExportRepository(),
        ).execute(
            ExportTasksRequest(
                filters=TaskExportFilters(),
                export_date='2026-07-17',
                include_groups=False,
                include_topics=False,
            ),
        ).payload

        self.assertNotIn('analog_groups', payload)
        self.assertNotIn('topics', payload)
        self.assertEqual(len(payload['tasks']), 2)
