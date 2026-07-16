from unittest import TestCase

from core_logic.use_cases.get_task_group_detail import GetTaskGroupDetailUseCase


class FakeTaskRepository:
    def __init__(self):
        self.detail_groups = ['group-1']
        self.detail_tasks = ['task-group-1']
        self.requested_group_id = None

    def get_detail_task_groups(self):
        return self.detail_groups

    def get_tasks_for_analog_group(self, group_id):
        self.requested_group_id = group_id
        return self.detail_tasks


class GetTaskGroupDetailUseCaseTests(TestCase):
    def test_get_queryset_returns_detail_groups(self):
        repo = FakeTaskRepository()
        use_case = GetTaskGroupDetailUseCase(task_repo=repo)

        self.assertEqual(use_case.get_queryset(), ['group-1'])

    def test_execute_returns_detail_tasks(self):
        repo = FakeTaskRepository()
        use_case = GetTaskGroupDetailUseCase(task_repo=repo)

        data = use_case.execute('group-1')

        self.assertEqual(repo.requested_group_id, 'group-1')
        self.assertEqual(data.tasks, ['task-group-1'])
