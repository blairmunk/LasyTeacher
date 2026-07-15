from unittest import TestCase

from core_logic.use_cases.delete_task import DeleteTaskRequest, DeleteTaskUseCase


class FakeTaskRepository:
    def __init__(self):
        self.deleted_task_id = None

    def delete_task(self, task_id):
        self.deleted_task_id = task_id
        return 1


class DeleteTaskUseCaseTests(TestCase):
    def test_execute_deletes_task(self):
        repo = FakeTaskRepository()
        use_case = DeleteTaskUseCase(task_repo=repo)

        result = use_case.execute(DeleteTaskRequest(task_id='task-1'))

        self.assertTrue(result.success)
        self.assertEqual(repo.deleted_task_id, 'task-1')
        self.assertEqual(result.deleted_count, 1)
        self.assertEqual(result.message, 'Задание успешно удалено!')

    def test_execute_rejects_empty_task_id(self):
        repo = FakeTaskRepository()
        use_case = DeleteTaskUseCase(task_repo=repo)

        result = use_case.execute(DeleteTaskRequest(task_id=''))

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty_task')
        self.assertIsNone(repo.deleted_task_id)
