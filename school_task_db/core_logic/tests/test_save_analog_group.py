from unittest import TestCase

from core_logic.use_cases.save_analog_group import (
    CreateAnalogGroupUseCase,
    SaveAnalogGroupRequest,
    UpdateAnalogGroupUseCase,
)


class FakeTaskRepository:
    def __init__(self):
        self.created_request = None
        self.updated_request = None
        self.update_exists = True

    def create_analog_group(self, name, description=''):
        self.created_request = (name, description)
        return 'created-group'

    def update_analog_group(self, group_id, name, description=''):
        self.updated_request = (group_id, name, description)
        return self.update_exists


class SaveAnalogGroupUseCaseTests(TestCase):
    def test_create_analog_group_delegates_to_repository(self):
        repo = FakeTaskRepository()
        use_case = CreateAnalogGroupUseCase(task_repo=repo)

        result = use_case.execute(
            SaveAnalogGroupRequest(
                name='Скорость',
                description='Описание',
            )
        )

        self.assertEqual(result.status, 'created')
        self.assertEqual(result.group_id, 'created-group')
        self.assertEqual(repo.created_request, ('Скорость', 'Описание'))

    def test_update_analog_group_delegates_to_repository(self):
        repo = FakeTaskRepository()
        use_case = UpdateAnalogGroupUseCase(task_repo=repo)

        result = use_case.execute(
            SaveAnalogGroupRequest(
                group_id='group-1',
                name='Скорость',
                description='Описание',
            )
        )

        self.assertEqual(result.status, 'updated')
        self.assertEqual(result.group_id, 'group-1')
        self.assertEqual(repo.updated_request, ('group-1', 'Скорость', 'Описание'))

    def test_update_analog_group_returns_not_found(self):
        repo = FakeTaskRepository()
        repo.update_exists = False
        use_case = UpdateAnalogGroupUseCase(task_repo=repo)

        result = use_case.execute(
            SaveAnalogGroupRequest(
                group_id='missing-group',
                name='Скорость',
            )
        )

        self.assertEqual(result.status, 'not_found')
        self.assertEqual(result.group_id, '')
