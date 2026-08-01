from datetime import datetime
from unittest import TestCase

from core_logic.value_objects.review_session import (
    review_session_is_completed,
    review_session_progress_percentage,
)


class ReviewSessionValueTests(TestCase):
    def test_calculates_review_session_progress(self):
        self.assertEqual(review_session_progress_percentage(3, 2), 66.7)
        self.assertEqual(review_session_progress_percentage(0, 0), 0)

    def test_detects_completed_session(self):
        self.assertFalse(review_session_is_completed(None))
        self.assertTrue(review_session_is_completed(datetime(2026, 8, 1)))
