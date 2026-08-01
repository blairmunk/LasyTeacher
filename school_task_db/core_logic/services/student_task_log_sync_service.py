"""Build the learning-history projection for a saved mark."""

from core_logic.entities.student import (
    TaskLogSyncEntry,
    TaskLogSyncPlan,
    TaskLogSyncSource,
)
from core_logic.value_objects.task_scores import (
    normalize_task_scores,
    resolve_task_score_record,
)


class StudentTaskLogSyncService:
    def build(self, source: TaskLogSyncSource) -> TaskLogSyncPlan:
        tasks = {task.task_id: task for task in source.tasks}
        entries = []
        for variant_task_id, score_record in self._resolved_scores(source):
            task = tasks.get(score_record.task_id)
            if task is None:
                continue
            percentage, is_correct = self._result_values(
                score_record.points,
                score_record.max_points,
            )
            entries.append(
                TaskLogSyncEntry(
                    mark_id=source.mark_id,
                    student_id=source.student_id,
                    task_id=task.task_id,
                    event_id=source.event_id,
                    variant_id=source.variant_id,
                    variant_task_id=variant_task_id or None,
                    topic_id=task.topic_id,
                    subtopic_id=task.subtopic_id,
                    analog_group_id=task.analog_group_id,
                    difficulty=task.difficulty,
                    points=score_record.points,
                    max_points=score_record.max_points,
                    comment=score_record.comment,
                    completed_at=source.completed_at,
                    percentage=percentage,
                    is_correct=is_correct,
                )
            )
        return TaskLogSyncPlan(mark_id=source.mark_id, entries=tuple(entries))

    @staticmethod
    def _resolved_scores(source):
        if source.variant_id:
            resolved = []
            for variant_task in source.variant_tasks:
                score_record = resolve_task_score_record(
                    source.task_scores,
                    variant_task_id=variant_task.variant_task_id,
                    task_id=variant_task.task_id,
                )
                if score_record:
                    resolved.append(
                        (variant_task.variant_task_id, score_record)
                    )
            return resolved
        return [
            ('', score_record)
            for score_record in normalize_task_scores(source.task_scores)
        ]

    @staticmethod
    def _result_values(points, max_points):
        if points is None or not max_points or max_points <= 0:
            return None, None
        percentage = round((points / max_points) * 100, 1)
        return percentage, percentage >= 70
