from unittest import TestCase

from core_logic.value_objects.analog_group_difficulty import (
    DEFAULT_ANALOG_GROUP_DIFFICULTY,
    resolve_analog_group_difficulty,
)


class AnalogGroupDifficultyTests(TestCase):
    def test_explicit_difficulty_has_priority(self):
        self.assertEqual(
            resolve_analog_group_difficulty(5, [1, 2, 3]),
            5,
        )

    def test_automatic_difficulty_uses_task_median(self):
        self.assertEqual(
            resolve_analog_group_difficulty(0, [1, 3, 5]),
            3,
        )

    def test_empty_group_uses_default_difficulty(self):
        self.assertEqual(
            resolve_analog_group_difficulty(0, []),
            DEFAULT_ANALOG_GROUP_DIFFICULTY,
        )
