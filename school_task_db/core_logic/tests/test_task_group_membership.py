from unittest import TestCase

from core_logic.use_cases.change_task_group_membership import (
    AddTasksToGroupRequest,
    AddTasksToGroupUseCase,
    RemoveTaskFromGroupRequest,
    RemoveTaskFromGroupUseCase,
)
from core_logic.value_objects.variant_print_plan import TASK_BANK_ROLE_DEMO


class FakeTaskRepository:
    def __init__(self):
        self.group_name = 'Скорость'
        self.added_request = None
        self.removed_request = None

    def get_analog_group_name(self, group_id):
        return self.group_name

    def add_tasks_to_group(self, group_id, task_ids, bank_role='control'):
        self.added_request = (group_id, task_ids, bank_role)
        return len(task_ids)

    def remove_task_from_group(self, group_id, task_id):
        self.removed_request = (group_id, task_id)
        return 1


class TaskGroupMembershipUseCaseTests(TestCase):
    def test_add_tasks_to_group_filters_empty_ids(self):
        repo = FakeTaskRepository()
        use_case = AddTasksToGroupUseCase(task_repo=repo)

        result = use_case.execute(
            AddTasksToGroupRequest(
                group_id='group-1',
                task_ids=['task-1', '', 'task-2'],
                bank_role=TASK_BANK_ROLE_DEMO,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.group_name, 'Скорость')
        self.assertEqual(result.created_count, 2)
        self.assertEqual(
            repo.added_request,
            ('group-1', ['task-1', 'task-2'], TASK_BANK_ROLE_DEMO),
        )

    def test_add_tasks_to_group_rejects_unknown_bank_role(self):
        repo = FakeTaskRepository()
        use_case = AddTasksToGroupUseCase(task_repo=repo)

        result = use_case.execute(
            AddTasksToGroupRequest(
                group_id='group-1',
                task_ids=['task-1'],
                bank_role='any',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'invalid')
        self.assertIn('Unsupported specific task bank role', result.errors[0])
        self.assertIsNone(repo.added_request)

    def test_add_tasks_to_group_handles_missing_group(self):
        repo = FakeTaskRepository()
        repo.group_name = None
        use_case = AddTasksToGroupUseCase(task_repo=repo)

        result = use_case.execute(
            AddTasksToGroupRequest(group_id='missing', task_ids=['task-1'])
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(repo.added_request)

    def test_remove_task_from_group_delegates_to_repository(self):
        repo = FakeTaskRepository()
        use_case = RemoveTaskFromGroupUseCase(task_repo=repo)

        result = use_case.execute(
            RemoveTaskFromGroupRequest(group_id='group-1', task_id='task-1')
        )

        self.assertTrue(result.success)
        self.assertEqual(result.deleted_count, 1)
        self.assertEqual(repo.removed_request, ('group-1', 'task-1'))
