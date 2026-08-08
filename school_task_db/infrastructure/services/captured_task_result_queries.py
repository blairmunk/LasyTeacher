"""Read self-contained task results from latest captured attempts."""

from dataclasses import dataclass
from typing import Any

from infrastructure.services.attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from infrastructure.services.task_content_snapshots import (
    task_content_snapshot_from_mapping,
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


def latest_assessable_task_results(participation_ids):
    """Return assessable task facts from each participation's latest revision."""
    attempts = latest_attempts_by_participation(participation_ids)
    results = []
    for attempt in attempts.values():
        for task_result in attempt.captured_task_results:
            if not task_result.is_assessable_snapshot:
                continue
            try:
                task = task_content_snapshot_from_mapping(
                    task_result.task_content_snapshot,
                )
            except (TypeError, ValueError):
                continue
            max_points = (
                task_result.checked_max_points
                if task_result.checked_max_points is not None
                else task_result.expected_max_points_snapshot
            )
            results.append(CapturedTaskResult(
                student_id=attempt.student_id_snapshot,
                event_id=attempt.event_id_snapshot,
                event_name=attempt.event_name_snapshot,
                event_date=attempt.event_date_snapshot,
                captured_at=(
                    attempt.checked_at_snapshot or attempt.created_at
                ),
                work_id=attempt.work_id_snapshot,
                task=task,
                points=task_result.points or 0,
                max_points=max_points or 0,
                comment=task_result.comment,
            ))
    return results
