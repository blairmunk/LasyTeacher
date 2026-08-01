"""Pure assembly of a personalized remedial sheet."""

from core_logic.entities.work import (
    RemedialOriginalTaskRow,
    RemedialSheetData,
    RemedialSheetSource,
)
from core_logic.value_objects.task_scores import resolve_task_score_record


class RemedialSheetService:
    def build(self, source: RemedialSheetSource) -> RemedialSheetData:
        original_tasks = []
        for item in source.original_tasks:
            score = resolve_task_score_record(
                source.task_scores,
                variant_task_id=item.variant_task_id,
                task_id=item.task.pk,
            )
            points = score.points if score else None
            max_points = score.max_points if score else None
            pct, status = self._score_status(points, max_points)
            original_tasks.append(RemedialOriginalTaskRow(
                task=item.task,
                order=item.order,
                points=points,
                max_points=max_points,
                pct=pct,
                status=status,
                group_name=item.group_name,
            ))

        return RemedialSheetData(
            variant=source.variant,
            student=source.student,
            source_work=source.source_work,
            mark=source.mark,
            original_tasks=original_tasks,
            new_tasks=source.new_tasks,
            content_blocks=source.content_blocks,
        )

    @staticmethod
    def _score_status(points, max_points):
        if (
            isinstance(points, (int, float))
            and isinstance(max_points, (int, float))
            and max_points > 0
        ):
            pct = points / max_points * 100
            if pct >= 70:
                status = 'ok'
            elif pct > 0:
                status = 'partial'
            else:
                status = 'fail'
            return round(pct, 1), status
        return 0, 'unknown'
