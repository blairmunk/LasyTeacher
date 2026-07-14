from unittest import TestCase

from core_logic.entities.event import (
    EventParticipationRow,
    EventStudentRef,
    EventVariantRef,
)
from core_logic.services.event_service import EventService
from core_logic.use_cases.get_event_detail import GetEventDetailUseCase
from core_logic.use_cases.get_event_list import GetEventListUseCase


class FakeEventRepository:
    def __init__(self):
        class Event:
            def __init__(self, status):
                self.status = status

        self.events = [Event('planned'), Event('graded')]

    def get_list_events(self):
        return self.events

    def get_detail_participations(self, event_id):
        return [
            EventParticipationRow(
                pk='p1',
                status='completed',
                student=EventStudentRef(
                    pk='s1',
                    last_name='Иванов',
                    first_name='Иван',
                ),
                variant=EventVariantRef(pk='v1', number=1),
            )
        ]

    def get_available_variants(self, event_id):
        return [EventVariantRef(pk='v1', number=1)]


class EventListAndDetailUseCaseTests(TestCase):
    def test_event_list_use_case_returns_categorized_events(self):
        use_case = GetEventListUseCase(
            event_repo=FakeEventRepository(),
            event_service=EventService(),
        )

        result = use_case.execute()

        self.assertEqual(len(result.events), 2)
        self.assertEqual(result.planned_events[0].status, 'planned')
        self.assertEqual(result.graded_events[0].status, 'graded')

    def test_event_detail_use_case_returns_status_and_participation_data(self):
        use_case = GetEventDetailUseCase(
            event_repo=FakeEventRepository(),
            event_service=EventService(),
        )

        result = use_case.execute(
            event_id='event-1',
            status='completed',
            has_work=True,
        )

        self.assertTrue(result.can_review)
        self.assertEqual(result.participations[0].student.last_name, 'Иванов')
        self.assertEqual(result.available_variants[0].number, 1)
