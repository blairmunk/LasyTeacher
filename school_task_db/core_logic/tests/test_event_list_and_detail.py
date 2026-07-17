from unittest import TestCase

from core_logic.entities.event import (
    EventEntity,
    EventParticipationRow,
    EventParticipationRef,
    EventStudentRef,
    EventVariantRef,
)
from core_logic.services.event_service import EventService
from core_logic.use_cases.get_event_detail import GetEventDetailUseCase
from core_logic.use_cases.get_event_list import GetEventListUseCase
from core_logic.use_cases.get_event_participant_selection import (
    GetEventParticipantSelectionUseCase,
)
from core_logic.use_cases.get_event_participation_ref import (
    GetEventParticipationRefUseCase,
)
from core_logic.use_cases.get_event_variant_assignment import (
    GetEventVariantAssignmentUseCase,
)


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

    def get_by_id(self, event_id):
        if event_id == 'missing':
            return None
        return EventEntity(
            id=event_id,
            name='КР',
            work_id='work-1',
            work_name='Контрольная',
            status='completed',
            status_display='Завершено',
            short_uuid='abcd1234',
            work_type='test',
            work_type_display='Контрольная работа',
        )

    def get_participation_ref(self, participation_id):
        if participation_id == 'missing':
            return None
        return EventParticipationRef(id=participation_id, event_id='event-1')


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

        result = use_case.execute(event_id='event-1')

        self.assertEqual(result.event.name, 'КР')
        self.assertTrue(result.can_review)
        self.assertEqual(result.participations[0].student.last_name, 'Иванов')
        self.assertEqual(result.available_variants[0].number, 1)

    def test_event_detail_use_case_returns_empty_data_for_missing_event(self):
        use_case = GetEventDetailUseCase(
            event_repo=FakeEventRepository(),
            event_service=EventService(),
        )

        result = use_case.execute(event_id='missing')

        self.assertIsNone(result.event)
        self.assertEqual(result.participations, [])

    def test_event_participant_selection_returns_current_participants(self):
        use_case = GetEventParticipantSelectionUseCase(
            event_repo=FakeEventRepository(),
        )

        result = use_case.execute(event_id='event-1')

        self.assertEqual(result.event.name, 'КР')
        self.assertEqual(len(result.current_participants), 1)
        self.assertEqual(
            result.current_participants[0].student.first_name,
            'Иван',
        )

    def test_event_participant_selection_returns_not_found_status(self):
        use_case = GetEventParticipantSelectionUseCase(
            event_repo=FakeEventRepository(),
        )

        result = use_case.execute(event_id='missing')

        self.assertEqual(result.status, 'not_found')
        self.assertEqual(result.current_participants, [])

    def test_event_variant_assignment_returns_participations_and_variants(self):
        use_case = GetEventVariantAssignmentUseCase(
            event_repo=FakeEventRepository(),
        )

        result = use_case.execute(event_id='event-1')

        self.assertEqual(result.event.name, 'КР')
        self.assertEqual(result.participations[0].pk, 'p1')
        self.assertEqual(result.variants[0].pk, 'v1')

    def test_event_participation_ref_returns_reference(self):
        use_case = GetEventParticipationRefUseCase(
            event_repo=FakeEventRepository(),
        )

        result = use_case.execute(participation_id='p1')

        self.assertEqual(result.participation.pk, 'p1')
        self.assertEqual(result.participation.event_id, 'event-1')

    def test_event_participation_ref_returns_not_found_status(self):
        use_case = GetEventParticipationRefUseCase(
            event_repo=FakeEventRepository(),
        )

        result = use_case.execute(participation_id='missing')

        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(result.participation)
