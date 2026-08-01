"""Difficulty rules for an analog group of tasks."""

import statistics
from collections.abc import Iterable


DEFAULT_ANALOG_GROUP_DIFFICULTY = 3


def resolve_analog_group_difficulty(
    nominal_difficulty: int,
    task_difficulties: Iterable[int],
) -> int:
    if nominal_difficulty and nominal_difficulty > 0:
        return nominal_difficulty
    difficulties = tuple(task_difficulties)
    if not difficulties:
        return DEFAULT_ANALOG_GROUP_DIFFICULTY
    return round(statistics.median(difficulties))
