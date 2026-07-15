from unittest import TestCase

from core_logic.use_cases.delete_task_groups import (
    DeleteTaskGroupsRequest,
    DeleteTaskGroupsUseCase,
)


class FakeTaskRepository:
    def __init__(self):
        self.deleted_group_ids = None

    def delete_groups(self, group_ids):
        self.deleted_group_ids = group_ids
        return len(group_ids)


class DeleteTaskGroupsUseCaseTests(TestCase):
    def test_execute_deletes_selected_groups(self):
        repo = FakeTaskRepository()
        use_case = DeleteTaskGroupsUseCase(task_repo=repo)

        result = use_case.execute(
            DeleteTaskGroupsRequest(group_ids=['group-1', '', 'group-2'])
        )

        self.assertTrue(result.success)
        self.assertEqual(result.deleted_count, 2)
        self.assertEqual(result.message, 'Удалено 2 групп')
        self.assertEqual(repo.deleted_group_ids, ['group-1', 'group-2'])

    def test_execute_rejects_empty_selection(self):
        repo = FakeTaskRepository()
        use_case = DeleteTaskGroupsUseCase(task_repo=repo)

        result = use_case.execute(DeleteTaskGroupsRequest(group_ids=[]))

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty_selection')
        self.assertIsNone(repo.deleted_group_ids)
