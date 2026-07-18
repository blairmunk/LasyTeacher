from unittest import TestCase

from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantRequest,
)
from core_logic.use_cases.change_event_status import ChangeEventStatusRequest
from core_logic.use_cases.prepare_event_action_submission import (
    PrepareAssignSingleVariantSubmissionUseCase,
    PrepareChangeEventStatusSubmissionUseCase,
    PrepareEventActionSubmissionRequest,
)


class PrepareEventActionSubmissionUseCaseTests(TestCase):
    def test_prepare_assign_single_variant_submission(self):
        result = PrepareAssignSingleVariantSubmissionUseCase().execute(
            PrepareEventActionSubmissionRequest(
                event_id='event-1',
                data={
                    'participation_id': ['participation-1'],
                    'variant_id': ['variant-1'],
                },
            )
        )

        self.assertEqual(
            result,
            AssignSingleEventVariantRequest(
                event_id='event-1',
                participation_id='participation-1',
                variant_id='variant-1',
            ),
        )

    def test_prepare_assign_single_variant_submission_uses_empty_defaults(self):
        result = PrepareAssignSingleVariantSubmissionUseCase().execute(
            PrepareEventActionSubmissionRequest(
                event_id='event-1',
                data={},
            )
        )

        self.assertEqual(result.participation_id, '')
        self.assertEqual(result.variant_id, '')

    def test_prepare_change_event_status_submission(self):
        result = PrepareChangeEventStatusSubmissionUseCase().execute(
            PrepareEventActionSubmissionRequest(
                event_id='event-1',
                data={'new_status': ['reviewing']},
            )
        )

        self.assertEqual(
            result,
            ChangeEventStatusRequest(
                event_id='event-1',
                new_status='reviewing',
            ),
        )
