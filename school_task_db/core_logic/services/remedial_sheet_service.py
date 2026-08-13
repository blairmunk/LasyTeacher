"""Pure assembly of a personalized remedial sheet."""

from decimal import Decimal, InvalidOperation

from core_logic.entities.work import (
    RemedialOriginalTaskRow,
    RemedialSheetData,
    RemedialSheetSource,
)
class RemedialSheetService:
    def build(self, source: RemedialSheetSource) -> RemedialSheetData:
        original_tasks = []
        for item in source.original_tasks:
            points = item.points
            max_points = item.max_points
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
            original_tasks=tuple(original_tasks),
            new_tasks=source.new_tasks,
            content_blocks=source.content_blocks,
        )

    @staticmethod
    def _score_status(points, max_points):
        try:
            points = Decimal(str(points))
            max_points = Decimal(str(max_points))
        except (InvalidOperation, TypeError, ValueError):
            return 0, 'unknown'
        if max_points <= 0:
            return 0, 'unknown'

        pct = float(points / max_points * 100)
        if pct >= 70:
            status = 'ok'
        elif pct > 0:
            status = 'partial'
        else:
            status = 'fail'
        return round(pct, 1), status
