from unittest import TestCase

from core_logic.entities.task import TaskExportFilters
from core_logic.use_cases.export_tasks import ExportTasksRequest, ExportTasksUseCase


class FakeTaskRepository:
    def __init__(self):
        self.filters = None
        self.export_date = None

    def build_task_export_payload(self, filters, export_date):
        self.filters = filters
        self.export_date = export_date
        return {'version': '1.1', 'tasks': []}


class ExportTasksUseCaseTests(TestCase):
    def test_execute_delegates_payload_building_to_repository(self):
        repo = FakeTaskRepository()
        filters = TaskExportFilters(topic_id='topic-1', subject='Физика', grade='9')
        use_case = ExportTasksUseCase(task_repo=repo)

        data = use_case.execute(
            ExportTasksRequest(filters=filters, export_date='2026-07-17'),
        )

        self.assertEqual(repo.filters, filters)
        self.assertEqual(repo.export_date, '2026-07-17')
        self.assertEqual(data.payload, {'version': '1.1', 'tasks': []})
