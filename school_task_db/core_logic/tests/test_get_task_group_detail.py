from unittest import TestCase

from core_logic.use_cases.get_task_group_detail import GetTaskGroupDetailUseCase


class FakeTaskRepository:
    def __init__(self):
        self.group = 'group-1'
        self.detail_tasks = ['task-group-1']
        self.requested_group_id = None

    def get_analog_group(self, group_id):
        return self.group if group_id == self.group else None

    def get_tasks_for_analog_group(self, group_id):
        self.requested_group_id = group_id
        return self.detail_tasks


class GetTaskGroupDetailUseCaseTests(TestCase):
    def test_execute_returns_detail_tasks(self):
        repo = FakeTaskRepository()
        use_case = GetTaskGroupDetailUseCase(task_repo=repo)

        data = use_case.execute('group-1')

        self.assertEqual(repo.requested_group_id, 'group-1')
        self.assertEqual(data.group, 'group-1')
        self.assertEqual(data.tasks, ['task-group-1'])

    def test_execute_returns_empty_data_for_missing_group(self):
        repo = FakeTaskRepository()
        use_case = GetTaskGroupDetailUseCase(task_repo=repo)

        data = use_case.execute('missing-group')

        self.assertIsNone(data.group)
        self.assertIsNone(data.tasks)
        self.assertIsNone(repo.requested_group_id)
