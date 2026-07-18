from unittest import TestCase

from core_logic.interfaces.work_repo import (
    CreateWorkAnalogGroupParams,
    CreateWorkParams,
)
from core_logic.use_cases.save_work import (
    CreateWorkUseCase,
    SaveWorkSpecificationRequest,
    SaveWorkSpecificationUseCase,
    UpdateWorkUseCase,
)


class FakeWorkRepository:
    def __init__(self, update_result=True):
        self.created_params = None
        self.updated_params = None
        self.replaced_specs = None
        self.update_result = update_result

    def create_work(self, params):
        self.created_params = params
        return 'work-1'

    def update_work(self, params):
        self.updated_params = params
        return self.update_result

    def replace_work_analog_groups(self, work_id, specs):
        self.replaced_specs = (work_id, specs)
        return self.update_result


class SaveWorkUseCaseTests(TestCase):
    def test_create_work_delegates_to_repository(self):
        repo = FakeWorkRepository()
        params = CreateWorkParams(
            name='КР',
            work_type='test',
            duration=45,
            max_score=10,
        )

        result = CreateWorkUseCase(repo).execute(params)

        self.assertEqual(result.status, 'created')
        self.assertEqual(result.work_id, 'work-1')
        self.assertEqual(repo.created_params, params)

    def test_update_work_delegates_to_repository(self):
        repo = FakeWorkRepository()
        params = CreateWorkParams(
            work_id='work-1',
            name='КР',
            work_type='quiz',
            duration=30,
            max_score=12,
        )

        result = UpdateWorkUseCase(repo).execute(params)

        self.assertEqual(result.status, 'updated')
        self.assertEqual(result.work_id, 'work-1')
        self.assertEqual(repo.updated_params, params)

    def test_update_work_returns_not_found(self):
        params = CreateWorkParams(work_id='missing', name='КР')

        result = UpdateWorkUseCase(FakeWorkRepository(False)).execute(params)

        self.assertEqual(result.status, 'not_found')

    def test_save_work_specification_replaces_specs(self):
        repo = FakeWorkRepository()
        specs = [
            CreateWorkAnalogGroupParams(
                work_id='work-1',
                analog_group_id='group-1',
                order=1,
                count=2,
                weight=3,
            )
        ]

        result = SaveWorkSpecificationUseCase(repo).execute(
            SaveWorkSpecificationRequest(work_id='work-1', specs=specs)
        )

        self.assertEqual(result.status, 'saved')
        self.assertEqual(result.saved_count, 1)
        self.assertEqual(repo.replaced_specs, ('work-1', specs))

    def test_save_work_specification_returns_not_found(self):
        result = SaveWorkSpecificationUseCase(FakeWorkRepository(False)).execute(
            SaveWorkSpecificationRequest(work_id='missing', specs=[])
        )

        self.assertEqual(result.status, 'not_found')
