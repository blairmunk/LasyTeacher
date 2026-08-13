"""Read self-contained task results from latest captured attempts."""

from core_logic.entities.attempt_snapshot import (
    CapturedAttemptTaskResult,
    CapturedStudentTaskResult,
)
from core_logic.value_objects.task_content_snapshot import (
    task_content_snapshot_from_mapping,
)
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)


def captured_task_result_snapshot(
    task_result,
) -> CapturedAttemptTaskResult | None:
    """Normalize one persisted task result without consulting live task data."""
    try:
        task = task_content_snapshot_from_mapping(
            task_result.task_content_snapshot,
        )
    except (TypeError, ValueError):
        return None
    max_points = (
        task_result.checked_max_points
        if task_result.checked_max_points is not None
        else task_result.expected_max_points_snapshot
    )
    return CapturedAttemptTaskResult(
        task=task,
        order=task_result.order_snapshot,
        points=_optional_float(task_result.points),
        max_points=float(max_points),
        comment=str(task_result.comment or ''),
        variant_task_id=str(task_result.variant_task_id or ''),
        source_selection_id=str(
            task_result.source_selection_id_snapshot or '',
        ),
        source_selection_name=str(
            task_result.source_selection_name_snapshot or '',
        ),
        content_order=task_result.content_order_snapshot,
        is_assessable=task_result.is_assessable_snapshot,
    )


def latest_assessable_task_results(participation_ids):
    """Return assessable task facts from each participation's latest revision."""
    attempts = latest_attempts_by_participation(participation_ids)
    results = []
    for attempt in attempts.values():
        for task_result in attempt.captured_task_results:
            captured = captured_task_result_snapshot(task_result)
            if captured is None or not captured.is_assessable:
                continue
            results.append(CapturedStudentTaskResult(
                student_id=attempt.student_id_snapshot,
                event_id=attempt.event_id_snapshot,
                event_name=attempt.event_name_snapshot,
                event_date=attempt.event_date_snapshot,
                captured_at=(
                    attempt.checked_at_snapshot or attempt.created_at
                ),
                work_id=attempt.work_id_snapshot,
                task=captured.task,
                points=captured.points or 0.0,
                max_points=captured.max_points,
                comment=captured.comment,
            ))
    return tuple(results)


def _optional_float(value) -> float | None:
    return float(value) if value is not None else None
