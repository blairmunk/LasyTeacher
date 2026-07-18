from unittest import TestCase

from core_logic.entities.task import TaskSaveParams, TaskSaveResult
from core_logic.use_cases.save_task import CreateTaskUseCase, UpdateTaskUseCase


class FakeTaskRepository:
    def __init__(self):
        self.created_params = None
        self.updated_params = None

    def create_task(self, params):
        self.created_params = params
        return TaskSaveResult(status='created', task_id='task-1')

    def update_task(self, params):
        self.updated_params = params
        return TaskSaveResult(status='updated', task_id=params.task_id)


class SaveTaskUseCaseTests(TestCase):
    def test_create_task_delegates_to_repository(self):
        repo = FakeTaskRepository()
        params = TaskSaveParams(
            text='Задача',
            answer='Ответ',
            topic_id='topic-1',
            task_type='computational',
            difficulty=2,
        )

        result = CreateTaskUseCase(repo).execute(params)

        self.assertEqual(result.task_id, 'task-1')
        self.assertEqual(repo.created_params, params)

    def test_update_task_delegates_to_repository(self):
        repo = FakeTaskRepository()
        params = TaskSaveParams(
            task_id='task-1',
            text='Задача',
            answer='Ответ',
            topic_id='topic-1',
            task_type='computational',
            difficulty=2,
        )

        result = UpdateTaskUseCase(repo).execute(params)

        self.assertEqual(result.status, 'updated')
        self.assertEqual(repo.updated_params, params)
