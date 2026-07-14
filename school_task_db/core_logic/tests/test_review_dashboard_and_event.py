from unittest import TestCase

from core_logic.entities.review import (
    EventReviewParticipationRow,
    ReviewEventProgress,
    ReviewEventRef,
    ReviewParticipationRef,
    ReviewStudentRef,
    ReviewVariantRef,
)
from core_logic.services.review_service import ReviewService
from core_logic.use_cases.get_event_review import GetEventReviewUseCase
from core_logic.use_cases.get_review_dashboard import GetReviewDashboardUseCase


class FakeReviewRepository:
    def __init__(self):
        self.event = ReviewEventRef(pk='event-1', name='КР', status='completed')
        self.student = ReviewStudentRef(pk='s1', last_name='Иванов', first_name='Иван')
        self.participation = ReviewParticipationRef(
            pk='p1',
            student=self.student,
            event=self.event,
            variant=ReviewVariantRef(pk='v1', number=1),
        )

    def get_dashboard_events(self):
        return [
            ReviewEventProgress(
                event=self.event,
                total_participants=1,
                active_participants=1,
                graded_participants=0,
                absent_participants=0,
                progress_percentage=0,
                remaining=1,
            )
        ]

    def get_event_review_participations(self, event_id):
        return [
            EventReviewParticipationRow(
                participation=self.participation,
                mark=None,
                has_mark=False,
                is_absent=False,
                student=self.student,
                variant=self.participation.variant,
            )
        ]

    def get_available_variants(self, event_id):
        return [ReviewVariantRef(pk='v1', number=1)]


class ReviewDashboardAndEventUseCaseTests(TestCase):
    def test_dashboard_use_case_returns_categorized_events(self):
        use_case = GetReviewDashboardUseCase(
            review_repo=FakeReviewRepository(),
            review_service=ReviewService(),
        )

        dashboard = use_case.execute()

        self.assertEqual(dashboard.needs_review[0].event.pk, 'event-1')
        self.assertEqual(dashboard.total_events, 1)

    def test_event_review_use_case_returns_event_review_data(self):
        use_case = GetEventReviewUseCase(
            review_repo=FakeReviewRepository(),
            review_service=ReviewService(),
        )

        review = use_case.execute('event-1')

        self.assertFalse(review.blocked)
        self.assertEqual(review.total_participants, 1)
        self.assertEqual(review.available_variants[0].pk, 'v1')
