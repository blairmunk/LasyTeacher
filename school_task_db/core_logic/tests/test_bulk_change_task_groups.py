from unittest import TestCase

from core_logic.use_cases.bulk_change_task_groups import (
    BulkAddTasksToGroupRequest,
    BulkAddTasksToGroupUseCase,
    BulkCreateGroupFromTasksRequest,
    BulkCreateGroupFromTasksUseCase,
    BulkRemoveTasksFromGroupsRequest,
    BulkRemoveTasksFromGroupsUseCase,
)


class FakeTaskRepository:
    def __init__(self):
        self.existing_task_ids = {'task-1', 'task-2'}
        self.group_names = {'group-1': 'Сила'}
        self.duplicate_group_names = set()
        self.created_groups = []
        self.added_requests = []
        self.removed_request = None

    def count_existing_task_ids(self, task_ids):
        return len(set(task_ids) & self.existing_task_ids)

    def analog_group_name_exists(self, name):
        return name in self.duplicate_group_names

    def create_analog_group(self, name, description=''):
        group_id = f'group-{len(self.created_groups) + 2}'
        self.created_groups.append((group_id, name, description))
        self.group_names[group_id] = name
        return group_id

    def get_analog_group_name(self, group_id):
        return self.group_names.get(group_id)

    def add_tasks_to_group(self, group_id, task_ids):
        self.added_requests.append((group_id, task_ids))
        return len([task_id for task_id in task_ids if task_id in self.existing_task_ids])

    def remove_tasks_from_all_groups(self, task_ids):
        self.removed_request = task_ids
        return len(task_ids)


class BulkChangeTaskGroupsUseCaseTests(TestCase):
    def test_create_group_from_tasks_creates_group_and_memberships(self):
        repo = FakeTaskRepository()
        use_case = BulkCreateGroupFromTasksUseCase(task_repo=repo)

        result = use_case.execute(
            BulkCreateGroupFromTasksRequest(
                task_ids=['task-1', '', 'task-2'],
                group_name='  Кинематика  ',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.group_id, 'group-2')
        self.assertEqual(result.group_name, 'Кинематика')
        self.assertEqual(result.added_count, 2)
        self.assertEqual(
            repo.created_groups,
            [('group-2', 'Кинематика', 'Создана из выбранных заданий')],
        )
        self.assertEqual(repo.added_requests, [('group-2', ['task-1', 'task-2'])])

    def test_create_group_rejects_duplicate_name(self):
        repo = FakeTaskRepository()
        repo.duplicate_group_names.add('Кинематика')
        use_case = BulkCreateGroupFromTasksUseCase(task_repo=repo)

        result = use_case.execute(
            BulkCreateGroupFromTasksRequest(
                task_ids=['task-1'],
                group_name='Кинематика',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'duplicate_name')
        self.assertEqual(repo.created_groups, [])

    def test_add_tasks_to_group_counts_existing_memberships_as_skipped(self):
        repo = FakeTaskRepository()
        use_case = BulkAddTasksToGroupUseCase(task_repo=repo)

        result = use_case.execute(
            BulkAddTasksToGroupRequest(
                task_ids=['task-1', 'task-2', 'missing-task'],
                group_id='group-1',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.added_count, 2)
        self.assertEqual(result.skipped_count, 0)
        self.assertEqual(
            repo.added_requests,
            [('group-1', ['task-1', 'task-2', 'missing-task'])],
        )

    def test_add_tasks_to_group_rejects_missing_group(self):
        repo = FakeTaskRepository()
        use_case = BulkAddTasksToGroupUseCase(task_repo=repo)

        result = use_case.execute(
            BulkAddTasksToGroupRequest(task_ids=['task-1'], group_id='missing')
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'missing_group')
        self.assertEqual(repo.added_requests, [])

    def test_remove_tasks_from_groups_delegates_filtered_ids(self):
        repo = FakeTaskRepository()
        use_case = BulkRemoveTasksFromGroupsUseCase(task_repo=repo)

        result = use_case.execute(
            BulkRemoveTasksFromGroupsRequest(task_ids=['task-1', '', 'task-2'])
        )

        self.assertTrue(result.success)
        self.assertEqual(result.removed_count, 2)
        self.assertEqual(repo.removed_request, ['task-1', 'task-2'])
