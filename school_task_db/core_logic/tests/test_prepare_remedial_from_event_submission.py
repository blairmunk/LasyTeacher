from unittest import TestCase

from core_logic.use_cases.create_remedial_from_event import RemedialFromEventRequest
from core_logic.use_cases.prepare_remedial_from_event_submission import (
    PrepareRemedialFromEventSubmissionRequest,
    PrepareRemedialFromEventSubmissionUseCase,
)


class PrepareRemedialFromEventSubmissionUseCaseTests(TestCase):
    def test_execute_prepares_creation_request(self):
        result = PrepareRemedialFromEventSubmissionUseCase().execute(
            PrepareRemedialFromEventSubmissionRequest(
                event_id='event-1',
                data={
                    'selected_students': ['student-1', 'student-2'],
                    'work_name': ['Работа над ошибками'],
                    'create_event': ['1'],
                    'event_date': ['2026-03-10'],
                },
            )
        )

        self.assertEqual(
            result,
            RemedialFromEventRequest(
                event_id='event-1',
                selected_student_ids=['student-1', 'student-2'],
                work_name='Работа над ошибками',
                create_event=True,
                event_date='2026-03-10',
            ),
        )

    def test_execute_uses_empty_defaults(self):
        result = PrepareRemedialFromEventSubmissionUseCase().execute(
            PrepareRemedialFromEventSubmissionRequest(
                event_id='event-1',
                data={},
            )
        )

        self.assertEqual(
            result,
            RemedialFromEventRequest(
                event_id='event-1',
                selected_student_ids=[],
                work_name='',
                create_event=False,
                event_date='',
            ),
        )
