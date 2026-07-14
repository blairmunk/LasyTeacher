from unittest import TestCase

from core_logic.entities.review import (
    ReviewEventRef,
    ReviewParticipationStatusChange,
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
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentRequest,
    ToggleParticipationAbsentUseCase,
)


class FakeReviewActionRepository:
    def __init__(self):
        self.finalized_event_id = None
        self.toggled_participation_id = None

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
