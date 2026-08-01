"""Resolve per-task grading records without persistence dependencies."""

from core_logic.entities.student import TaskResult
from core_logic.value_objects.task_scores import (
    normalize_task_scores,
    resolve_task_score_record,
)


class StudentTaskResultService:
    def build(self, source):
        if source is None:
            return []
        if source.variant_tasks:
            resolved = []
            for row in source.variant_tasks:
                record = resolve_task_score_record(
                    source.task_scores,
                    variant_task_id=row.variant_task_id,
                    task_id=row.task_id,
                )
                if record:
                    resolved.append((row.variant_task_id, record))
        else:
            resolved = [
                ('', record)
                for record in normalize_task_scores(source.task_scores)
            ]

        groups = {group.task_id: group for group in source.groups}
        return [
            TaskResult(
                task_id=record.task_id,
                variant_task_id=variant_task_id,
                points=record.points,
                max_points=record.max_points,
                group_id=(
                    groups[record.task_id].group_id
                    if record.task_id in groups
                    else None
                ),
                group_name=(
                    groups[record.task_id].group_name
                    if record.task_id in groups
                    else ''
                ),
            )
            for variant_task_id, record in resolved
        ]
