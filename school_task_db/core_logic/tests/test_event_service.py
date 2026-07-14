from unittest import TestCase

from core_logic.entities.event import (
    EventParticipationRow,
    EventStudentRef,
    EventVariantRef,
)
from core_logic.services.event_service import EventService


class EventServiceTests(TestCase):
    def test_build_list_data_categorizes_events_by_status(self):
        class Event:
            def __init__(self, status):
                self.status = status

        planned = Event('planned')
        completed = Event('completed')
        reviewing = Event('reviewing')
        graded = Event('graded')

        data = EventService().build_list_data([
            planned,
            completed,
            reviewing,
            graded,
        ])

        self.assertEqual(data.planned_events, [planned])
        self.assertEqual(data.active_events, [completed, reviewing])
        self.assertEqual(data.graded_events, [graded])

    def test_build_detail_data_calculates_review_flags_and_status_ui(self):
        student = EventStudentRef(pk='s1', last_name='Иванов', first_name='Иван')

        detail = EventService().build_detail_data(
            status='completed',
            has_work=True,
            participations=[
                EventParticipationRow(
                    pk='p1',
                    status='completed',
                    student=student,
                    variant=EventVariantRef(pk='v1', number=1),
                )
            ],
            available_variants=[EventVariantRef(pk='v1', number=1)],
        )

        self.assertTrue(detail.some_variants_assigned)
        self.assertTrue(detail.all_variants_assigned)
        self.assertTrue(detail.can_review)
        self.assertEqual(detail.status_color, 'info')
        self.assertEqual(detail.status_steps[2].code, 'completed')
        self.assertTrue(detail.status_steps[2].current)
        self.assertEqual(detail.status_transitions[0].new_status, 'reviewing')

    def test_status_transition_rules_and_labels_are_pure(self):
        service = EventService()

        self.assertTrue(service.can_change_status('completed', 'reviewing'))
        self.assertFalse(service.can_change_status('completed', 'closed'))
        self.assertEqual(service.status_label('reviewing'), 'На проверке')
        self.assertEqual(service.status_label('unknown'), 'unknown')
