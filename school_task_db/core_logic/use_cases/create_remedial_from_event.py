"""Create remedial work from an existing event."""

from dataclasses import dataclass, field
from typing import List, Optional

from core_logic.interfaces.event_attempt_repo import IEventAttemptRepository
from core_logic.interfaces.event_repo import CreateEventParams, IEventRepository
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
from core_logic.services.remedial_service import (
    REMEDIAL_SOURCE_EVENT_STATUSES,
    RemedialSelectionLimits,
    RemedialService,
)
from core_logic.services.remedial_variant_content_service import (
    build_remedial_variant_creation_plan,
)


@dataclass(frozen=True)
class RemedialFromEventRequest:
    event_id: str
    selected_student_ids: List[str]
    work_name: str = ''
    create_event: bool = False
    event_date: Optional[str] = None
    tasks_per_group: int = 1
    max_total_tasks: int = 10


@dataclass(frozen=True)
class RemedialFromEventResult:
    success: bool
    work_id: Optional[str] = None
    event_id: Optional[str] = None
    variants_created: int = 0
    students_without_tasks: int = 0
    students_without_review: int = 0
    students_with_shortage: int = 0
    message: str = ''
    errors: List[str] = field(default_factory=list)


class CreateRemedialFromEventUseCase:
    def __init__(
        self,
        remedial_service: RemedialService,
        task_repo: ITaskSelectionRepository,
        work_repo: IWorkVariantCreationRepository,
        event_repo: IEventRepository,
        event_attempt_repo: IEventAttemptRepository,
        transaction_manager: ITransactionManager,
    ):
        self.remedial_service = remedial_service
        self.task_repo = task_repo
        self.work_repo = work_repo
        self.event_repo = event_repo
        self.event_attempt_repo = event_attempt_repo
        self.transaction_manager = transaction_manager

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
        if event.status not in REMEDIAL_SOURCE_EVENT_STATUSES:
            return RemedialFromEventResult(
                success=False,
                message=(
                    'Работу над ошибками можно создать только после '
                    'начала проверки события.'
                ),
            )

        selections = []
        attempts_by_student_id = {}
        students_without_tasks = 0
        students_without_review = 0
        students_with_shortage = 0
        try:
            limits = RemedialSelectionLimits(
                tasks_per_group=request.tasks_per_group,
                max_total_tasks=request.max_total_tasks,
            )
        except ValueError:
            return RemedialFromEventResult(
                success=False,
                message='Количество заданий должно быть больше нуля.',
            )
        for student_id in request.selected_student_ids:
            attempt = self.event_attempt_repo.get_latest_student_attempt(
                request.event_id,
                student_id,
            )
            if attempt is None or not attempt.attempt_snapshot_id:
                students_without_review += 1
                continue
            attempts_by_student_id[student_id] = attempt
            selection = self.remedial_service.select_tasks_for_student(
                student_id=student_id,
                event_id=request.event_id,
                mark_score=attempt.score,
                limits=limits,
            )
            if selection.shortage_count:
                students_with_shortage += 1
            if selection.task_ids:
                selections.append(selection)
            else:
                students_without_tasks += 1

        if not selections:
            if students_without_tasks and students_without_review:
                message = (
                    'Для проверенных работ не осталось доступных '
                    'заданий-аналогов; часть выбранных работ ещё не проверена.'
                )
            elif students_without_tasks:
                message = (
                    'Для выбранных проверенных работ не осталось '
                    'доступных заданий-аналогов.'
                )
            else:
                message = 'У выбранных учеников нет проверенных результатов.'
            return RemedialFromEventResult(
                success=False,
                students_without_tasks=students_without_tasks,
                students_without_review=students_without_review,
                students_with_shortage=students_with_shortage,
                message=message,
            )

        work_name = request.work_name or f'Работа над ошибками — {event.work_name}'
        selection_plans = [
            build_remedial_variant_creation_plan(
                task_ids=selection.task_ids,
                tasks=self.task_repo.get_by_ids(set(selection.task_ids)),
                number=number,
                work_name=work_name,
            )
            for number, selection in enumerate(
                selections,
                start=1,
            )
        ]
        max_score = max(
            (plan.max_score_snapshot for plan in selection_plans),
            default=0,
        )

        with self.transaction_manager.atomic():
            created_work = self.work_repo.create_work_with_variants(
                CreateWorkWithVariantsParams(
                    work=CreateWorkParams(
                        name=work_name,
                        work_type='remedial',
                        max_score=max_score,
                        variant_counter=len(selections),
                    ),
                    variants=[
                        NewWorkVariantParams(
                            student_id=selection.student_id,
                            plan=plan,
                            source_work_id=event.work_id,
                            source_participation_id=(
                                attempts_by_student_id[
                                    selection.student_id
                                ].participation_id
                                or None
                            ),
                            source_attempt_snapshot_id=(
                                attempts_by_student_id[
                                    selection.student_id
                                ].attempt_snapshot_id
                                or None
                            ),
                        )
                        for selection, plan in zip(
                            selections,
                            selection_plans,
                        )
                    ],
                )
            )
            work_id = created_work.work_id
            variant_ids = [
                (selection.student_id, variant_id)
                for selection, variant_id in zip(
                    selections,
                    created_work.variant_ids,
                )
            ]

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
        if students_without_tasks:
            message += (
                f' Для {students_without_tasks} учеников не осталось '
                'доступных аналогов.'
            )
        if students_without_review:
            message += (
                f' Для {students_without_review} учеников проверка ещё не '
                'завершена или не зафиксирована.'
            )
        if students_with_shortage and not students_without_tasks:
            message += (
                f' Для {students_with_shortage} учеников доступно меньше '
                'заданий, чем запрошено.'
            )

        return RemedialFromEventResult(
            success=True,
            work_id=work_id,
            event_id=new_event_id,
            variants_created=len(selections),
            students_without_tasks=students_without_tasks,
            students_without_review=students_without_review,
            students_with_shortage=students_with_shortage,
            message=message,
        )
