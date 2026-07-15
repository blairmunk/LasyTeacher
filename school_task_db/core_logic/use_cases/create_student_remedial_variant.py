"""Create an orphan remedial variant for one student."""

from dataclasses import dataclass
from typing import List

from core_logic.interfaces.student_repo import IStudentRepository
from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.interfaces.work_repo import CreateVariantParams, IWorkRepository


@dataclass(frozen=True)
class CreateStudentRemedialVariantRequest:
    student_id: str
    max_tasks: int = 10
    selected_group_ids: List[str] = None

    def group_ids(self) -> List[str]:
        return self.selected_group_ids or []


@dataclass(frozen=True)
class CreateStudentRemedialVariantResult:
    success: bool
    message: str
    variant_id: str = ''
    task_count: int = 0
    total_score: int = 0


class CreateStudentRemedialVariantUseCase:
    def __init__(
        self,
        student_repo: IStudentRepository,
        task_repo: ITaskRepository,
        work_repo: IWorkRepository,
    ):
        self.student_repo = student_repo
        self.task_repo = task_repo
        self.work_repo = work_repo

    def execute(
        self,
        request: CreateStudentRemedialVariantRequest,
    ) -> CreateStudentRemedialVariantResult:
        task_ids = self.student_repo.select_student_remedial_task_ids(
            student_id=request.student_id,
            max_tasks=request.max_tasks,
            selected_group_ids=request.group_ids(),
        )
        if not task_ids:
            return CreateStudentRemedialVariantResult(
                success=False,
                message='Нет доступных заданий для работы над ошибками.',
            )

        tasks = self.task_repo.get_by_ids(set(task_ids))
        if not tasks:
            return CreateStudentRemedialVariantResult(
                success=False,
                message='Нет доступных заданий для работы над ошибками.',
            )

        total_score = sum(task.difficulty or 1 for task in tasks)
        student_name = self.student_repo.get_student_short_name(request.student_id)
        variant_id = self.work_repo.create_variant_with_tasks(
            CreateVariantParams(
                work_id=None,
                number=1,
                student_id=request.student_id,
                task_ids=task_ids,
                work_name_snapshot=f'Работа над ошибками — {student_name}',
                max_score_snapshot=total_score,
                variant_type='remedial',
            )
        )

        return CreateStudentRemedialVariantResult(
            success=True,
            variant_id=variant_id,
            task_count=len(tasks),
            total_score=total_score,
            message=(
                f'Создан вариант «Работа над ошибками» для {student_name}: '
                f'{len(tasks)} заданий, макс. балл: {total_score}'
            ),
        )
