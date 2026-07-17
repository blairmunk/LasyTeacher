from unittest import TestCase

from core_logic.use_cases.get_add_tasks_to_group import (
    AddTasksToGroupFormRequest,
    GetAddTasksToGroupUseCase,
)


class FakeTaskRepository:
    def __init__(self, group='group-1'):
        self.group = group
        self.available_tasks = ['task-2']
        self.available_request = None

    def get_analog_group(self, group_id):
        return self.group

    def get_available_tasks_for_analog_group(self, group_id, search):
        self.available_request = (group_id, search)
        return self.available_tasks


class GetAddTasksToGroupUseCaseTests(TestCase):
    def test_execute_returns_group_and_available_tasks(self):
        repo = FakeTaskRepository()
        use_case = GetAddTasksToGroupUseCase(task_repo=repo)

        data = use_case.execute(
            AddTasksToGroupFormRequest(group_id='group-1', search='скорость'),
        )

        self.assertEqual(data.status, 'ready')
        self.assertEqual(data.group, 'group-1')
        self.assertEqual(data.available_tasks, ['task-2'])
        self.assertEqual(data.search, 'скорость')
        self.assertEqual(repo.available_request, ('group-1', 'скорость'))

    def test_execute_returns_not_found_without_loading_available_tasks(self):
        repo = FakeTaskRepository(group=None)
        use_case = GetAddTasksToGroupUseCase(task_repo=repo)

        data = use_case.execute(
            AddTasksToGroupFormRequest(group_id='missing', search='x'),
        )

        self.assertEqual(data.status, 'not_found')
        self.assertEqual(data.search, 'x')
        self.assertIsNone(repo.available_request)
