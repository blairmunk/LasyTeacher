from unittest import TestCase

from core_logic.interfaces.work_repo import (
    CreateWorkAnalogGroupParams,
    CreateWorkParams,
)
from core_logic.use_cases.create_work_from_groups import (
    CreateWorkFromGroupsRequest,
    CreateWorkFromGroupsUseCase,
    GroupSpecRequest,
)


class FakeTaskRepository:
    def __init__(self):
        self.existing_count = 2
        self.first_difficulties = {'group-1': 3}
        self.requested_group_ids = None

    def count_existing_group_ids(self, group_ids):
        self.requested_group_ids = group_ids
        return self.existing_count

    def get_first_task_difficulty_for_group(self, group_id):
        return self.first_difficulties.get(group_id, 1)


class FakeWorkRepository:
    def __init__(self):
        self.created_work = None
        self.created_groups = []
        self.generated_variants = None

    def create_work(self, params: CreateWorkParams):
        self.created_work = params
        return 'work-1'

    def create_work_analog_group(self, params: CreateWorkAnalogGroupParams):
        self.created_groups.append(params)

    def compose_variants(self, work_id, count):
        self.generated_variants = (work_id, count)
        return count


class CreateWorkFromGroupsUseCaseTests(TestCase):
    def test_execute_creates_work_spec_and_generates_variants(self):
        task_repo = FakeTaskRepository()
        work_repo = FakeWorkRepository()
        use_case = CreateWorkFromGroupsUseCase(
            task_repo=task_repo,
            work_repo=work_repo,
        )

        result = use_case.execute(
            CreateWorkFromGroupsRequest(
                groups=[
                    GroupSpecRequest(id='group-1', order=1, count=2, weight=0),
                    GroupSpecRequest(id='group-2', order=2, count=1, weight=5),
                ],
                work_name='  Контрольная  ',
                work_type='quiz',
                max_score=10,
                auto_generate=True,
                variant_count=3,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.work_id, 'work-1')
        self.assertEqual(result.variants_generated, 3)
        self.assertEqual(task_repo.requested_group_ids, {'group-1', 'group-2'})
        self.assertEqual(
            work_repo.created_work,
            CreateWorkParams(name='Контрольная', work_type='quiz', max_score=10),
        )
        self.assertEqual(
            work_repo.created_groups,
            [
                CreateWorkAnalogGroupParams(
                    work_id='work-1',
                    analog_group_id='group-1',
                    order=1,
                    count=2,
                    weight=3,
                ),
                CreateWorkAnalogGroupParams(
                    work_id='work-1',
                    analog_group_id='group-2',
                    order=2,
                    count=1,
                    weight=5,
                ),
            ],
        )
        self.assertEqual(work_repo.generated_variants, ('work-1', 3))
        self.assertIn('3 вариантами', result.message)

    def test_execute_rejects_empty_groups(self):
        use_case = CreateWorkFromGroupsUseCase(
            task_repo=FakeTaskRepository(),
            work_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            CreateWorkFromGroupsRequest(groups=[], work_name='Контрольная')
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty_groups')

    def test_execute_rejects_missing_groups(self):
        task_repo = FakeTaskRepository()
        task_repo.existing_count = 1
        work_repo = FakeWorkRepository()
        use_case = CreateWorkFromGroupsUseCase(
            task_repo=task_repo,
            work_repo=work_repo,
        )

        result = use_case.execute(
            CreateWorkFromGroupsRequest(
                groups=[
                    GroupSpecRequest(id='group-1'),
                    GroupSpecRequest(id='group-2'),
                ],
                work_name='Контрольная',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'missing_groups')
        self.assertIsNone(work_repo.created_work)
