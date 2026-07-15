from unittest import TestCase

from core_logic.interfaces.work_repo import (
    CreatedWorkVariantRef,
    CreateWorkWithVariantFromTasksParams,
)
from core_logic.use_cases.create_work_from_tasks import (
    CreateWorkFromTasksRequest,
    CreateWorkFromTasksUseCase,
)


class FakeTaskRepository:
    def __init__(self):
        self.existing_task_ids = {'task-1', 'task-2'}
        self.requested_task_ids = None

    def count_existing_task_ids(self, task_ids):
        self.requested_task_ids = task_ids
        return len(set(task_ids) & self.existing_task_ids)


class FakeWorkRepository:
    def __init__(self):
        self.created_params = None

    def create_work_with_variant_from_tasks(self, params):
        self.created_params = params
        return CreatedWorkVariantRef(
            work_id='work-1',
            variant_id='variant-1',
            tasks_count=2,
        )


class CreateWorkFromTasksUseCaseTests(TestCase):
    def test_execute_creates_work_and_first_variant(self):
        task_repo = FakeTaskRepository()
        work_repo = FakeWorkRepository()
        use_case = CreateWorkFromTasksUseCase(
            task_repo=task_repo,
            work_repo=work_repo,
        )

        result = use_case.execute(
            CreateWorkFromTasksRequest(
                task_ids=['task-1', '', 'task-2'],
                work_name='  Проверочная  ',
                work_type='quiz',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.work_id, 'work-1')
        self.assertEqual(result.variant_id, 'variant-1')
        self.assertEqual(result.tasks_count, 2)
        self.assertEqual(task_repo.requested_task_ids, {'task-1', 'task-2'})
        self.assertEqual(
            work_repo.created_params,
            CreateWorkWithVariantFromTasksParams(
                name='Проверочная',
                work_type='quiz',
                task_ids=['task-1', 'task-2'],
            ),
        )

    def test_execute_rejects_empty_task_selection(self):
        work_repo = FakeWorkRepository()
        use_case = CreateWorkFromTasksUseCase(
            task_repo=FakeTaskRepository(),
            work_repo=work_repo,
        )

        result = use_case.execute(
            CreateWorkFromTasksRequest(task_ids=[], work_name='Проверочная')
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty_tasks')
        self.assertIsNone(work_repo.created_params)

    def test_execute_rejects_empty_work_name(self):
        work_repo = FakeWorkRepository()
        use_case = CreateWorkFromTasksUseCase(
            task_repo=FakeTaskRepository(),
            work_repo=work_repo,
        )

        result = use_case.execute(
            CreateWorkFromTasksRequest(task_ids=['task-1'], work_name='  ')
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty_name')
        self.assertIsNone(work_repo.created_params)

    def test_execute_rejects_missing_tasks(self):
        work_repo = FakeWorkRepository()
        use_case = CreateWorkFromTasksUseCase(
            task_repo=FakeTaskRepository(),
            work_repo=work_repo,
        )

        result = use_case.execute(
            CreateWorkFromTasksRequest(
                task_ids=['missing-task'],
                work_name='Проверочная',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'missing_tasks')
        self.assertIsNone(work_repo.created_params)
