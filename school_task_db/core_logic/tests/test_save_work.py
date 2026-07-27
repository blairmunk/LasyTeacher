from unittest import TestCase

from core_logic.interfaces.work_repo import (
    CreateWorkParams,
    CreateWorkWithSpecificationParams,
    WorkTaskSelectionParams,
)
from core_logic.use_cases.save_work import (
    CreateWorkWithSpecificationUseCase,
    SaveWorkSpecificationRequest,
    SaveWorkSpecificationUseCase,
    UpdateWorkUseCase,
)
from core_logic.value_objects.task_print_settings import TASK_BANK_ROLE_DEMO


class FakeWorkRepository:
    def __init__(self, update_result=True):
        self.updated_params = None
        self.replaced_specs = None
        self.created_with_specification = None
        self.update_result = update_result

    def create_work_with_specification(self, params):
        self.created_with_specification = params
        return 'work-with-specification'

    def update_work(self, params):
        self.updated_params = params
        return self.update_result

    def replace_work_analog_groups(self, work_id, specs):
        self.replaced_specs = (work_id, specs)
        return self.update_result


class SaveWorkUseCaseTests(TestCase):
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

    def test_create_work_with_specification_validates_and_delegates(self):
        repo = FakeWorkRepository()
        params = CreateWorkWithSpecificationParams(
            work=CreateWorkParams(name='Рабочий лист'),
            specs=[
                WorkTaskSelectionParams(
                    analog_group_id='group-1',
                    order=1,
                    count=2,
                    weight=3,
                )
            ],
        )

        result = CreateWorkWithSpecificationUseCase(repo).execute(params)

        self.assertEqual(result.status, 'created')
        self.assertEqual(result.work_id, 'work-with-specification')
        self.assertEqual(repo.created_with_specification, params)

    def test_create_work_with_specification_rejects_invalid_specs(self):
        repo = FakeWorkRepository()
        params = CreateWorkWithSpecificationParams(
            work=CreateWorkParams(name='Рабочий лист'),
            specs=[
                WorkTaskSelectionParams(
                    analog_group_id='group-1',
                    order=1,
                    count=1,
                    weight=1,
                    blank_cells_rows=0,
                )
            ],
        )

        result = CreateWorkWithSpecificationUseCase(repo).execute(params)

        self.assertEqual(result.status, 'invalid')
        self.assertIn('blank_cells_rows must be positive', result.errors[0])
        self.assertIsNone(repo.created_with_specification)

    def test_update_work_returns_not_found(self):
        params = CreateWorkParams(work_id='missing', name='КР')

        result = UpdateWorkUseCase(FakeWorkRepository(False)).execute(params)

        self.assertEqual(result.status, 'not_found')

    def test_save_work_specification_replaces_specs(self):
        repo = FakeWorkRepository()
        specs = [
            WorkTaskSelectionParams(
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

    def test_save_work_specification_rejects_invalid_spec_rows(self):
        repo = FakeWorkRepository()

        result = SaveWorkSpecificationUseCase(repo).execute(
            SaveWorkSpecificationRequest(
                work_id='work-1',
                specs=[
                    WorkTaskSelectionParams(
                        analog_group_id='group-1',
                        order=1,
                        count=1,
                        weight=1,
                        bank_role_filter=TASK_BANK_ROLE_DEMO,
                        blank_cells_rows=0,
                    )
                ],
            )
        )

        self.assertEqual(result.status, 'invalid')
        self.assertIn('blank_cells_rows must be positive', result.errors[0])
        self.assertIsNone(repo.replaced_specs)

    def test_save_work_specification_returns_not_found(self):
        result = SaveWorkSpecificationUseCase(FakeWorkRepository(False)).execute(
            SaveWorkSpecificationRequest(work_id='missing', specs=[])
        )

        self.assertEqual(result.status, 'not_found')
