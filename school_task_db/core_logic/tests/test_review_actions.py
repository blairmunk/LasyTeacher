from unittest import TestCase

from core_logic.entities.review import (
    ReviewEventRef,
    ReviewParticipationStatusChange,
    ReviewSaveNavigation,
)
from core_logic.services.review_service import ReviewService
from core_logic.use_cases.calculate_review_score import (
    CalculateReviewScoreRequest,
    CalculateReviewScoreUseCase,
)
from core_logic.use_cases.finalize_review_event import (
    FinalizeReviewEventRequest,
    FinalizeReviewEventUseCase,
)
from core_logic.use_cases.get_review_save_navigation import (
    GetReviewSaveNavigationRequest,
    GetReviewSaveNavigationUseCase,
)
from core_logic.use_cases.prepare_participation_review_submission import (
    PrepareParticipationReviewSubmissionRequest,
    PrepareParticipationReviewSubmissionUseCase,
)
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentRequest,
    ToggleParticipationAbsentUseCase,
)
from core_logic.use_cases.validate_review_work_scan import (
    ValidateReviewWorkScanRequest,
    ValidateReviewWorkScanUseCase,
)


class FakeReviewActionRepository:
    def __init__(self):
        self.finalized_event_id = None
        self.toggled_participation_id = None
        self.navigation_participation_id = None

    def finalize_event(self, event_id):
        self.finalized_event_id = event_id
        return ReviewEventRef(pk=event_id, name='КР 9А', status='graded')

    def toggle_absent(self, participation_id):
        self.toggled_participation_id = participation_id
        return ReviewParticipationStatusChange(
            participation_id=participation_id,
            event_id='event-1',
            student_last_name='Иванов',
            status='absent',
            is_absent=True,
        )

    def get_save_navigation(self, participation_id):
        self.navigation_participation_id = participation_id
        return ReviewSaveNavigation(event_id='event-1', all_checked=True)


class ReviewActionUseCaseTests(TestCase):
    def test_calculate_review_score_parses_values_and_uses_service(self):
        use_case = CalculateReviewScoreUseCase(review_service=ReviewService())

        result = use_case.execute(
            CalculateReviewScoreRequest(points='7', max_points='10')
        )

        self.assertEqual(result.score, 4)
        self.assertEqual(result.percentage, 70)

    def test_calculate_review_score_tolerates_bad_values(self):
        use_case = CalculateReviewScoreUseCase(review_service=ReviewService())

        result = use_case.execute(
            CalculateReviewScoreRequest(points='', max_points='bad')
        )

        self.assertEqual(result.score, 2)
        self.assertEqual(result.percentage, 0)

    def test_finalize_review_event_delegates_to_repository(self):
        repo = FakeReviewActionRepository()
        use_case = FinalizeReviewEventUseCase(review_repo=repo)

        result = use_case.execute(FinalizeReviewEventRequest(event_id='event-1'))

        self.assertEqual(result.name, 'КР 9А')
        self.assertEqual(repo.finalized_event_id, 'event-1')

    def test_toggle_participation_absent_delegates_to_repository(self):
        repo = FakeReviewActionRepository()
        use_case = ToggleParticipationAbsentUseCase(review_repo=repo)

        result = use_case.execute(
            ToggleParticipationAbsentRequest(participation_id='participation-1')
        )

        self.assertTrue(result.is_absent)
        self.assertEqual(result.student_last_name, 'Иванов')
        self.assertEqual(repo.toggled_participation_id, 'participation-1')

    def test_prepare_submission_use_case_uses_review_service(self):
        use_case = PrepareParticipationReviewSubmissionUseCase(
            review_service=ReviewService(),
        )

        result = use_case.execute(
            PrepareParticipationReviewSubmissionRequest(
                data={'score': '5', 'task_t1': '3', 'task_t1_max': '3'},
            )
        )

        self.assertEqual(result.score, 5)
        self.assertEqual(result.task_scores['t1']['points'], 3)

    def test_validate_work_scan_use_case_uses_review_service(self):
        use_case = ValidateReviewWorkScanUseCase(review_service=ReviewService())

        result = use_case.execute(
            ValidateReviewWorkScanRequest(
                size=1024,
                content_type='image/png',
            )
        )

        self.assertTrue(result.accepted)

    def test_get_review_save_navigation_delegates_to_repository(self):
        repo = FakeReviewActionRepository()
        use_case = GetReviewSaveNavigationUseCase(review_repo=repo)

        result = use_case.execute(
            GetReviewSaveNavigationRequest(participation_id='participation-1')
        )

        self.assertTrue(result.all_checked)
        self.assertEqual(repo.navigation_participation_id, 'participation-1')
