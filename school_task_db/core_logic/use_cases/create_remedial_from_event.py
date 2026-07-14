"""Create remedial work from an existing event."""

from dataclasses import dataclass, field
from typing import List, Optional

from core_logic.interfaces.event_repo import CreateEventParams, IEventRepository
from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.interfaces.work_repo import (
    CreateVariantParams,
    CreateWorkParams,
    IWorkRepository,
)
from core_logic.services.remedial_service import (
    RemedialService,
    RemedialTaskSelection,
)


@dataclass(frozen=True)
class RemedialFromEventRequest:
    event_id: str
    selected_student_ids: List[str]
    work_name: str = ''
    create_event: bool = False
    event_date: Optional[str] = None


@dataclass(frozen=True)
class RemedialFromEventResult:
    success: bool
    work_id: Optional[str] = None
    event_id: Optional[str] = None
    variants_created: int = 0
    message: str = ''
    errors: List[str] = field(default_factory=list)


class CreateRemedialFromEventUseCase:
    def __init__(
        self,
        remedial_service: RemedialService,
        task_repo: ITaskRepository,
        work_repo: IWorkRepository,
        event_repo: IEventRepository,
    ):
        self.remedial_service = remedial_service
        self.task_repo = task_repo
        self.work_repo = work_repo
        self.event_repo = event_repo

    def execute(
        self,
        request: RemedialFromEventRequest,
    ) -> RemedialFromEventResult:
        if not request.selected_student_ids:
            return RemedialFromEventResult(
                success=False,
                message='Не выбрано ни одного ученика.',
            )

        event = self.event_repo.get_by_id(request.event_id)
        if not event:
            return RemedialFromEventResult(
                success=False,
                message='Событие не найдено.',
            )

        selections = []
        for student_id in request.selected_student_ids:
            mark = self.event_repo.get_student_mark(request.event_id, student_id)
            selection = self.remedial_service.select_tasks_for_student(
                student_id=student_id,
                event_id=request.event_id,
                source_work_id=event.work_id,
                mark_score=mark.score if mark else None,
            )
            if selection.task_ids:
                selections.append(selection)

        if not selections:
            return RemedialFromEventResult(
                success=False,
                message='Нет доступных заданий для выбранных учеников.',
            )

        work_name = request.work_name or f'Работа над ошибками — {event.work_name}'
        selection_scores = [
            self._total_difficulty(selection)
            for selection in selections
        ]
        max_score = max(selection_scores) if selection_scores else 0

        work_id = self.work_repo.create_work(
            CreateWorkParams(
                name=work_name,
                work_type='remedial',
                max_score=max_score,
                variant_counter=len(selections),
            )
        )

        variant_ids = []
        for number, selection in enumerate(selections, 1):
            total_score = self._total_difficulty(selection)
            variant_id = self.work_repo.create_variant_with_tasks(
                CreateVariantParams(
                    work_id=work_id,
                    number=number,
                    student_id=selection.student_id,
                    task_ids=selection.task_ids,
                    work_name_snapshot=work_name,
                    max_score_snapshot=total_score,
                    source_work_id=event.work_id,
                    variant_type='remedial',
                )
            )
            variant_ids.append((selection.student_id, variant_id))

        new_event_id = None
        if request.create_event:
            new_event_id = self.event_repo.create_event(
                CreateEventParams(
                    name=work_name,
                    work_id=work_id,
                    date=request.event_date,
                    course_id=event.course_id,
                    description=f'Работа над ошибками по: {event.work_name}',
                )
            )
            for student_id, variant_id in variant_ids:
                self.event_repo.create_participation(
                    event_id=new_event_id,
                    student_id=student_id,
                    variant_id=variant_id,
                )

        message = f'Создана работа «{work_name}» с {len(selections)} вариантами.'
        if new_event_id:
            message += ' Событие создано.'

        return RemedialFromEventResult(
            success=True,
            work_id=work_id,
            event_id=new_event_id,
            variants_created=len(selections),
            message=message,
        )

    def _total_difficulty(self, selection: RemedialTaskSelection) -> int:
        tasks = self.task_repo.get_by_ids(set(selection.task_ids))
        return sum(task.difficulty or 1 for task in tasks)
