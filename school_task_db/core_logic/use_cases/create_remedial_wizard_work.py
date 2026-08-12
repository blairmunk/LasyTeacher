"""Create remedial work, variants and optional event from wizard step 3."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from core_logic.interfaces.event_participation_repo import (
    IEventParticipationRepository,
)
from core_logic.interfaces.event_commands import CreateEventParams
from core_logic.interfaces.event_write_repo import IEventWriteRepository
from core_logic.interfaces.student_group_catalog_repo import (
    IStudentGroupCatalogRepository,
)
from core_logic.interfaces.task_selection_repo import ITaskSelectionRepository
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.interfaces.work_commands import (
    CreateWorkParams,
    CreateWorkWithVariantsParams,
    NewWorkVariantParams,
)
from core_logic.interfaces.work_variant_creation_repo import (
    IWorkVariantCreationRepository,
)
from core_logic.services.remedial_variant_content_service import (
    build_remedial_variant_creation_plan,
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
        student_repo: IStudentGroupCatalogRepository,
        task_repo: ITaskSelectionRepository,
        work_repo: IWorkVariantCreationRepository,
        event_write_repo: IEventWriteRepository,
        event_participation_repo: IEventParticipationRepository,
        transaction_manager: ITransactionManager,
    ):
        self.student_repo = student_repo
        self.task_repo = task_repo
        self.work_repo = work_repo
        self.event_write_repo = event_write_repo
        self.event_participation_repo = event_participation_repo
        self.transaction_manager = transaction_manager

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

        student_plans = {}
        for student_id, task_ids in student_task_ids.items():
            plan = build_remedial_variant_creation_plan(
                task_ids=task_ids,
                tasks=self.task_repo.get_by_ids(set(task_ids)),
                number=len(student_plans) + 1,
                work_name=request.work_name,
            )
            if plan.tasks:
                student_plans[student_id] = plan
        if not student_plans:
            return CreateRemedialWizardWorkResult(
                success=False,
                message='Нет заданий для выбранных учеников.',
                status='empty_tasks',
            )
        max_score = max(
            plan.max_score_snapshot
            for plan in student_plans.values()
        )
        with self.transaction_manager.atomic():
            created_work = self.work_repo.create_work_with_variants(
                CreateWorkWithVariantsParams(
                    work=CreateWorkParams(
                        name=request.work_name,
                        work_type='remedial',
                        max_score=max_score,
                        variant_counter=len(student_plans),
                    ),
                    variants=[
                        NewWorkVariantParams(
                            student_id=student_id,
                            plan=plan,
                        )
                        for student_id, plan in student_plans.items()
                    ],
                )
            )
            work_id = created_work.work_id
            variant_ids = [
                (student_id, variant_id)
                for student_id, variant_id in zip(
                    student_plans,
                    created_work.variant_ids,
                )
            ]

            event_id = None
            if request.create_event:
                group_name = self.student_repo.get_group_name(request.group_id)
                event_id = self.event_write_repo.create_event(
                    CreateEventParams(
                        name=request.work_name,
                        work_id=work_id,
                        date=request.event_date,
                        description=f'Работа над ошибками для {group_name}',
                    )
                )
                for student_id, variant_id in variant_ids:
                    self.event_participation_repo.create_participation(
                        event_id=event_id,
                        student_id=student_id,
                        variant_id=variant_id,
                    )

        message = (
            f'Создана работа «{request.work_name}» '
            f'с {len(student_plans)} вариантами.'
        )
        if event_id:
            message += f' Событие на {request.event_date} создано.'

        return CreateRemedialWizardWorkResult(
            success=True,
            message=message,
            work_id=work_id,
            event_id=event_id,
            variants_created=len(student_plans),
        )
