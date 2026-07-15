"""Create remedial work, variants and optional event from wizard step 3."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from core_logic.interfaces.event_repo import CreateEventParams, IEventRepository
from core_logic.interfaces.student_repo import IStudentRepository
from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.interfaces.work_repo import (
    CreateVariantParams,
    CreateWorkParams,
    IWorkRepository,
)


@dataclass(frozen=True)
class CreateRemedialWizardWorkRequest:
    group_id: str
    selected_student_ids: List[str]
    student_task_ids: Dict[str, List[str]]
    work_name: str = 'Работа над ошибками'
    create_event: bool = False
    event_date: str = ''


@dataclass(frozen=True)
class CreateRemedialWizardWorkResult:
    success: bool
    message: str
    work_id: str = ''
    event_id: Optional[str] = None
    variants_created: int = 0
    status: str = 'created'


class CreateRemedialWizardWorkUseCase:
    def __init__(
        self,
        student_repo: IStudentRepository,
        task_repo: ITaskRepository,
        work_repo: IWorkRepository,
        event_repo: IEventRepository,
    ):
        self.student_repo = student_repo
        self.task_repo = task_repo
        self.work_repo = work_repo
        self.event_repo = event_repo

    def execute(
        self,
        request: CreateRemedialWizardWorkRequest,
    ) -> CreateRemedialWizardWorkResult:
        if not self.student_repo.get_group_name(request.group_id):
            return CreateRemedialWizardWorkResult(
                success=False,
                message='Класс не найден.',
                status='group_not_found',
            )

        if not request.selected_student_ids:
            return CreateRemedialWizardWorkResult(
                success=False,
                message='Не выбрано ни одного ученика.',
                status='empty_selection',
            )

        student_task_ids = {
            student_id: request.student_task_ids[student_id]
            for student_id in request.selected_student_ids
            if request.student_task_ids.get(student_id)
        }
        if not student_task_ids:
            return CreateRemedialWizardWorkResult(
                success=False,
                message='Нет заданий для выбранных учеников.',
                status='empty_tasks',
            )

        max_score = max(
            self._total_difficulty(task_ids)
            for task_ids in student_task_ids.values()
        )
        work_id = self.work_repo.create_work(
            CreateWorkParams(
                name=request.work_name,
                work_type='remedial',
                max_score=max_score,
                variant_counter=len(student_task_ids),
            )
        )

        variant_ids = []
        for number, (student_id, task_ids) in enumerate(
            student_task_ids.items(),
            1,
        ):
            variant_id = self.work_repo.create_variant_with_tasks(
                CreateVariantParams(
                    work_id=work_id,
                    number=number,
                    student_id=student_id,
                    task_ids=task_ids,
                    work_name_snapshot=request.work_name,
                    max_score_snapshot=self._total_difficulty(task_ids),
                    variant_type='remedial',
                )
            )
            variant_ids.append((student_id, variant_id))

        event_id = None
        if request.create_event:
            group_name = self.student_repo.get_group_name(request.group_id)
            event_id = self.event_repo.create_event(
                CreateEventParams(
                    name=request.work_name,
                    work_id=work_id,
                    date=request.event_date,
                    description=f'Работа над ошибками для {group_name}',
                )
            )
            for student_id, variant_id in variant_ids:
                self.event_repo.create_participation(
                    event_id=event_id,
                    student_id=student_id,
                    variant_id=variant_id,
                )

        message = (
            f'Создана работа «{request.work_name}» '
            f'с {len(student_task_ids)} вариантами.'
        )
        if event_id:
            message += f' Событие на {request.event_date} создано.'

        return CreateRemedialWizardWorkResult(
            success=True,
            message=message,
            work_id=work_id,
            event_id=event_id,
            variants_created=len(student_task_ids),
        )

    def _total_difficulty(self, task_ids: List[str]) -> int:
        tasks = self.task_repo.get_by_ids(set(task_ids))
        return sum(task.difficulty or 1 for task in tasks)
