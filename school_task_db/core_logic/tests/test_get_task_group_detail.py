from unittest import TestCase

from core_logic.entities.task import TaskGroupDetailGroup, TaskGroupDetailTask
from core_logic.use_cases.get_task_group_detail import GetTaskGroupDetailUseCase


class FakeTaskRepository:
    def __init__(self):
        self.group = TaskGroupDetailGroup(pk='group-1', name='Скорость')
        self.detail_tasks = [
            TaskGroupDetailTask(
                pk='task-1',
                topic='Кинематика',
                text='Задача',
                task_type_display='Расчётная задача',
                difficulty_display='Средняя',
            )
        ]
        self.requested_group_id = None

    def get_analog_group_detail(self, group_id):
        return self.group if group_id == self.group.pk else None

    def get_task_group_detail_tasks(self, group_id):
        self.requested_group_id = group_id
        return self.detail_tasks


class GetTaskGroupDetailUseCaseTests(TestCase):
    def test_execute_returns_detail_tasks(self):
        repo = FakeTaskRepository()
        use_case = GetTaskGroupDetailUseCase(task_repo=repo)

        data = use_case.execute('group-1')

        self.assertEqual(repo.requested_group_id, 'group-1')
        self.assertEqual(data.group, repo.group)
        self.assertEqual(data.tasks, repo.detail_tasks)

    def test_execute_returns_empty_data_for_missing_group(self):
        repo = FakeTaskRepository()
        use_case = GetTaskGroupDetailUseCase(task_repo=repo)

        data = use_case.execute('missing-group')

        self.assertIsNone(data.group)
        self.assertIsNone(data.tasks)
        self.assertIsNone(repo.requested_group_id)
