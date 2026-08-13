from unittest import TestCase
import datetime as dt

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
                    'tasks_per_group': ['3'],
                    'max_total_tasks': ['12'],
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
                event_date=dt.date(2026, 3, 10),
                tasks_per_group=3,
                max_total_tasks=12,
            ),
        )

    def test_execute_bounds_invalid_task_limits(self):
        result = PrepareRemedialFromEventSubmissionUseCase().execute(
            PrepareRemedialFromEventSubmissionRequest(
                event_id='event-1',
                data={
                    'tasks_per_group': ['0'],
                    'max_total_tasks': ['500'],
                },
            )
        )

        self.assertEqual(result.tasks_per_group, 1)
        self.assertEqual(result.max_total_tasks, 50)

    def test_execute_rejects_invalid_event_date(self):
        result = PrepareRemedialFromEventSubmissionUseCase().execute(
            PrepareRemedialFromEventSubmissionRequest(
                event_id='event-1',
                data={'event_date': ['not-a-date']},
            ),
        )

        self.assertIsNone(result.event_date)

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
                event_date=None,
            ),
        )
