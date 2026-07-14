"""Build remedial-from-event preview data."""

from dataclasses import dataclass, field
from typing import List, Optional

from core_logic.entities.event import EventEntity, WorkSummary
from core_logic.interfaces.event_repo import IEventRepository


@dataclass(frozen=True)
class RemedialEventPreviewResult:
    success: bool
    event: Optional[EventEntity] = None
    work: Optional[WorkSummary] = None
    analysis: List[dict] = field(default_factory=list)
    weak_students: int = 0
    message: str = ''


class GetRemedialEventPreviewUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(self, event_id: str) -> RemedialEventPreviewResult:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            return RemedialEventPreviewResult(
                success=False,
                message='Событие не найдено.',
            )

        analysis = [
            self._analyze_participation(item)
            for item in self.event_repo.get_participation_marks(event_id)
        ]
        weak_students = sum(
            1
            for row in analysis
            if row.get('status') in ('weak', 'needs_attention')
        )

        return RemedialEventPreviewResult(
            success=True,
            event=event,
            work=WorkSummary(id=event.work_id, name=event.work_name),
            analysis=analysis,
            weak_students=weak_students,
        )

    def _analyze_participation(self, item) -> dict:
        if item.score is None and item.points is None and item.max_points is None:
            return {
                'student': item.student,
                'variant': item.variant,
                'score_pct': None,
                'weak_tasks': [],
                'status': 'Не проверено',
            }

        max_points = float(item.max_points) if item.max_points else 0
        points = float(item.points) if item.points else 0
        score_pct = round(points / max_points * 100, 1) if max_points > 0 else 0

        weak_tasks = []
        for task_id, score_data in (item.task_scores or {}).items():
            if not isinstance(score_data, dict):
                continue

            task_points = score_data.get('points', 0)
            task_max_points = score_data.get('max_points', 1)
            if task_max_points <= 0:
                continue

            if task_max_points <= 2:
                is_weak = task_points == 0
            else:
                is_weak = task_points / task_max_points < 0.5

            if is_weak:
                weak_tasks.append(str(task_id))

        if item.score and item.score <= 2:
            status = 'weak'
        elif score_pct < 50:
            status = 'weak'
        elif score_pct < 70 or (item.score and item.score <= 3 and weak_tasks):
            status = 'needs_attention'
        else:
            status = 'ok'

        return {
            'student': item.student,
            'variant': item.variant,
            'score_pct': score_pct,
            'points': points,
            'max_points': max_points,
            'mark_score': item.score,
            'weak_tasks_count': len(weak_tasks),
            'weak_tasks': weak_tasks,
            'status': status,
        }
