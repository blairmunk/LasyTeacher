"""Validation rules for a student's aggregate mark."""


def validate_mark_values(score, points, max_points) -> None:
    if score and not 1 <= score <= 5:
        raise ValueError('Оценка должна быть от 1 до 5')
    if points and max_points and points > max_points:
        raise ValueError(
            'Набранные баллы не могут превышать максимум',
        )
