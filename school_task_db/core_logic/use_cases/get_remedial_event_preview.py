"""Build remedial-from-event preview data."""

from dataclasses import dataclass, field
from typing import Optional

from core_logic.entities.event import (
    EventEntity,
    ParticipationAttemptData,
    StudentSummary,
    VariantSummary,
    WorkSummary,
)
from core_logic.interfaces.event_attempt_repo import IEventAttemptRepository
from core_logic.interfaces.event_read_repo import IEventReadRepository
from core_logic.services.remedial_service import REMEDIAL_SOURCE_EVENT_STATUSES


@dataclass(frozen=True)
class RemedialEventPreviewItem:
    student: StudentSummary
    variant: Optional[VariantSummary]
    score_pct: Optional[float]
    points: Optional[float]
    max_points: Optional[float]
    mark_score: Optional[int]
    weak_tasks: tuple[str, ...] = field(default_factory=tuple)
    status: str = 'unchecked'

    def __post_init__(self):
        object.__setattr__(self, 'weak_tasks', tuple(self.weak_tasks))

    @property
    def weak_tasks_count(self) -> int:
        return len(self.weak_tasks)

    @property
    def is_checked(self) -> bool:
        return self.status != 'unchecked'

    @property
    def status_label(self) -> str:
        return {
            'weak': 'Нужна работа',
            'needs_attention': 'Внимание',
            'ok': 'OK',
            'unchecked': 'Не проверено',
        }.get(self.status, self.status)


@dataclass(frozen=True)
class RemedialEventPreviewResult:
    success: bool
    event: Optional[EventEntity] = None
    work: Optional[WorkSummary] = None
    analysis: tuple[RemedialEventPreviewItem, ...] = field(
        default_factory=tuple,
    )
    weak_students: int = 0
    message: str = ''


class GetRemedialEventPreviewUseCase:
    def __init__(
        self,
        event_repo: IEventReadRepository,
        event_attempt_repo: IEventAttemptRepository,
    ):
        self.event_repo = event_repo
        self.event_attempt_repo = event_attempt_repo

    def execute(self, event_id: str) -> RemedialEventPreviewResult:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            return RemedialEventPreviewResult(
                success=False,
                message='Событие не найдено.',
            )
        if event.status not in REMEDIAL_SOURCE_EVENT_STATUSES:
            return RemedialEventPreviewResult(
                success=False,
                message=(
                    'Работу над ошибками можно создать только после '
                    'начала проверки события.'
                ),
            )

        analysis = tuple(
            self._analyze_participation(item)
            for item in self.event_attempt_repo.get_participation_attempts(
                event_id,
            )
        )
        weak_students = sum(
            1
            for row in analysis
            if row.status in ('weak', 'needs_attention')
        )

        return RemedialEventPreviewResult(
            success=True,
            event=event,
            work=WorkSummary(id=event.work_id, name=event.work_name),
            analysis=analysis,
            weak_students=weak_students,
        )

    def _analyze_participation(
        self,
        item: ParticipationAttemptData,
    ) -> RemedialEventPreviewItem:
        if item.score is None and item.points is None and item.max_points is None:
            return RemedialEventPreviewItem(
                student=item.student,
                variant=item.variant,
                score_pct=None,
                points=None,
                max_points=None,
                mark_score=None,
            )

        max_points = float(item.max_points) if item.max_points else 0
        points = float(item.points) if item.points else 0
        score_pct = round(points / max_points * 100, 1) if max_points > 0 else 0

        weak_tasks = []
        for score_record in item.task_scores:
            task_points = score_record.points or 0
            task_max_points = score_record.max_points or 1
            if task_max_points <= 0:
                continue

            if task_max_points <= 2:
                is_weak = task_points == 0
            else:
                is_weak = task_points / task_max_points < 0.5

            if is_weak:
                weak_tasks.append(score_record.task_id)

        if item.score and item.score <= 2:
            status = 'weak'
        elif score_pct < 50:
            status = 'weak'
        elif score_pct < 70 or (item.score and item.score <= 3 and weak_tasks):
            status = 'needs_attention'
        else:
            status = 'ok'

        return RemedialEventPreviewItem(
            student=item.student,
            variant=item.variant,
            score_pct=score_pct,
            points=points,
            max_points=max_points,
            mark_score=item.score,
            weak_tasks=tuple(weak_tasks),
            status=status,
        )
