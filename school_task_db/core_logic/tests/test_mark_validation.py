from unittest import TestCase

from core_logic.value_objects.mark_validation import validate_mark_values


class MarkValidationTests(TestCase):
    def test_accepts_empty_and_valid_mark_values(self):
        validate_mark_values(None, None, None)
        validate_mark_values(5, 8, 10)

    def test_rejects_score_outside_supported_scale(self):
        with self.assertRaisesRegex(
            ValueError,
            'Оценка должна быть от 1 до 5',
        ):
            validate_mark_values(6, 8, 10)

    def test_rejects_points_above_maximum(self):
        with self.assertRaisesRegex(
            ValueError,
            'Набранные баллы не могут превышать максимум',
        ):
            validate_mark_values(4, 11, 10)
