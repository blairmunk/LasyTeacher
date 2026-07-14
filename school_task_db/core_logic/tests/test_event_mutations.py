from unittest import TestCase

from core_logic.entities.event import EventVariantAssignmentResult
from core_logic.services.event_service import EventService
from core_logic.use_cases.add_event_participants import (
    AddEventParticipantsRequest,
    AddEventParticipantsUseCase,
)
from core_logic.use_cases.assign_event_variants import (
    AssignEventVariantsRequest,
    AssignEventVariantsUseCase,
)
from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantRequest,
    AssignSingleEventVariantUseCase,
)
from core_logic.use_cases.change_event_status import (
    ChangeEventStatusRequest,
    ChangeEventStatusUseCase,
)


class FakeMutationEventRepository:
    def __init__(self):
        self.student_ids = []
        self.assignments = {}
        self.single_assignment = None
        self.status = 'completed'
        self.saved_status = None

    def add_participants(self, event_id, student_ids):
        self.student_ids = student_ids
        return len(student_ids)

    def assign_variants(self, event_id, assignments):
        self.assignments = assignments
        return len(assignments)

    def assign_variant(self, event_id, participation_id, variant_id):
        self.single_assignment = (event_id, participation_id, variant_id)
        return EventVariantAssignmentResult(
            variant_number=2,
            student_last_name='Иванов',
            student_first_name='Иван',
        )

    def get_event_status(self, event_id):
        return self.status

    def set_event_status(self, event_id, status):
        self.saved_status = status


class EventMutationUseCaseTests(TestCase):
    def test_add_participants_deduplicates_student_ids(self):
        repo = FakeMutationEventRepository()
        use_case = AddEventParticipantsUseCase(event_repo=repo)

        result = use_case.execute(
            AddEventParticipantsRequest(
                event_id='event-1',
                student_ids=['student-1', 'student-1', 'student-2'],
            )
        )

        self.assertEqual(result.created_count, 2)
        self.assertEqual(repo.student_ids, ['student-1', 'student-2'])

    def test_assign_event_variants_filters_empty_assignments(self):
        repo = FakeMutationEventRepository()
        use_case = AssignEventVariantsUseCase(event_repo=repo)

        result = use_case.execute(
            AssignEventVariantsRequest(
                event_id='event-1',
                assignments={'p1': 'v1', 'p2': '', '': 'v3'},
            )
        )

        self.assertEqual(result.assigned_count, 1)
        self.assertEqual(repo.assignments, {'p1': 'v1'})

    def test_assign_single_variant_requires_selection(self):
        repo = FakeMutationEventRepository()
        use_case = AssignSingleEventVariantUseCase(event_repo=repo)

        result = use_case.execute(
            AssignSingleEventVariantRequest(
                event_id='event-1',
                participation_id='',
                variant_id='v1',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, 'missing_selection')
        self.assertIsNone(repo.single_assignment)

    def test_assign_single_variant_returns_feedback_data(self):
        repo = FakeMutationEventRepository()
        use_case = AssignSingleEventVariantUseCase(event_repo=repo)

        result = use_case.execute(
            AssignSingleEventVariantRequest(
                event_id='event-1',
                participation_id='p1',
                variant_id='v1',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.assignment.variant_number, 2)
        self.assertEqual(result.assignment.student_name, 'Иванов Иван')
        self.assertEqual(repo.single_assignment, ('event-1', 'p1', 'v1'))

    def test_change_status_allows_known_transition(self):
        repo = FakeMutationEventRepository()
        use_case = ChangeEventStatusUseCase(
            event_repo=repo,
            event_service=EventService(),
        )

        result = use_case.execute(
            ChangeEventStatusRequest(
                event_id='event-1',
                new_status='reviewing',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.new_status_label, 'На проверке')
        self.assertEqual(repo.saved_status, 'reviewing')

    def test_change_status_rejects_unknown_transition(self):
        repo = FakeMutationEventRepository()
        use_case = ChangeEventStatusUseCase(
            event_repo=repo,
            event_service=EventService(),
        )

        result = use_case.execute(
            ChangeEventStatusRequest(
                event_id='event-1',
                new_status='closed',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(repo.saved_status, None)
