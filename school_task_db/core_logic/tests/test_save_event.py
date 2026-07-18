from unittest import TestCase

from core_logic.interfaces.event_repo import CreateEventParams
from core_logic.use_cases.save_event import (
    CreateEventUseCase,
    SaveEventResult,
    UpdateEventUseCase,
)


class FakeEventRepository:
    def __init__(self, update_result=True):
        self.created_params = None
        self.updated_params = None
        self.update_result = update_result

    def create_event(self, params):
        self.created_params = params
        return 'event-1'

    def update_event(self, params):
        self.updated_params = params
        return self.update_result


class SaveEventUseCaseTests(TestCase):
    def test_create_event_delegates_to_repository(self):
        repo = FakeEventRepository()
        params = CreateEventParams(
            name='КР',
            work_id='work-1',
            status='planned',
        )

        result = CreateEventUseCase(repo).execute(params)

        self.assertEqual(result, SaveEventResult(status='created', event_id='event-1'))
        self.assertEqual(repo.created_params, params)

    def test_update_event_delegates_to_repository(self):
        repo = FakeEventRepository()
        params = CreateEventParams(
            event_id='event-1',
            name='КР',
            work_id='work-1',
            status='completed',
        )

        result = UpdateEventUseCase(repo).execute(params)

        self.assertEqual(result.status, 'updated')
        self.assertEqual(result.event_id, 'event-1')
        self.assertEqual(repo.updated_params, params)

    def test_update_event_returns_not_found(self):
        params = CreateEventParams(
            event_id='missing',
            name='КР',
            work_id='work-1',
        )

        result = UpdateEventUseCase(FakeEventRepository(False)).execute(params)

        self.assertEqual(result.status, 'not_found')
