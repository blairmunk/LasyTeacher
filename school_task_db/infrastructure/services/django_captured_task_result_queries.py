"""Read self-contained task results from latest captured attempts."""

from dataclasses import dataclass
from typing import Any

from core_logic.value_objects.task_content_snapshot import (
    task_content_snapshot_from_mapping,
)
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)


@dataclass(frozen=True)
class CapturedTaskResult:
    student_id: str
    event_id: str
    event_name: str
    event_date: Any
    captured_at: Any
    work_id: str
    task: Any
    points: Any
    max_points: Any
    comment: str


@dataclass(frozen=True)
class CapturedTaskResultSnapshot:
    task: Any
    order: int
    points: Any
    max_points: Any
    comment: str
    source_selection_id: str
    source_selection_name: str
    content_order: int
    is_assessable: bool


def captured_task_result_snapshot(task_result):
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
    return CapturedTaskResultSnapshot(
        task=task,
        order=task_result.order_snapshot,
        points=task_result.points,
        max_points=max_points,
        comment=task_result.comment,
        source_selection_id=task_result.source_selection_id_snapshot,
        source_selection_name=task_result.source_selection_name_snapshot,
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
            results.append(CapturedTaskResult(
                student_id=attempt.student_id_snapshot,
                event_id=attempt.event_id_snapshot,
                event_name=attempt.event_name_snapshot,
                event_date=attempt.event_date_snapshot,
                captured_at=(
                    attempt.checked_at_snapshot or attempt.created_at
                ),
                work_id=attempt.work_id_snapshot,
                task=captured.task,
                points=captured.points or 0,
                max_points=captured.max_points or 0,
                comment=captured.comment,
            ))
    return results
