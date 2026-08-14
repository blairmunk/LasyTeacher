"""Create an orphan remedial variant for one student."""

from dataclasses import dataclass, field

from core_logic.interfaces.student_remedial_repo import (
    IStudentRemedialRepository,
)
from core_logic.interfaces.student_catalog_repo import IStudentCatalogRepository
from core_logic.interfaces.task_selection_repo import ITaskSelectionRepository
from core_logic.entities.work_variant_creation_commands import CreateVariantParams
from core_logic.interfaces.work_variant_creation_repo import (
    IWorkVariantCreationRepository,
)
from core_logic.services.student_remedial_service import StudentRemedialService
from core_logic.services.remedial_variant_content_service import (
    build_remedial_variant_creation_plan,
)


@dataclass(frozen=True)
class CreateStudentRemedialVariantRequest:
    student_id: str
    max_tasks: int = 10
    selected_group_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(
            self,
            'selected_group_ids',
            tuple(self.selected_group_ids),
        )


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
        student_repo: IStudentCatalogRepository,
        student_learning_repo: IStudentRemedialRepository,
        task_repo: ITaskSelectionRepository,
        work_repo: IWorkVariantCreationRepository,
        remedial_service: StudentRemedialService | None = None,
    ):
        self.student_repo = student_repo
        self.student_learning_repo = student_learning_repo
        self.task_repo = task_repo
        self.work_repo = work_repo
        self.remedial_service = remedial_service or StudentRemedialService()

    def execute(
        self,
        request: CreateStudentRemedialVariantRequest,
    ) -> CreateStudentRemedialVariantResult:
        task_ids = self.remedial_service.select_task_ids(
            self.student_learning_repo.get_student_remedial_source(
                request.student_id,
            ),
            max_tasks=request.max_tasks,
            selected_group_ids=request.selected_group_ids,
        )
        if not task_ids:
            return CreateStudentRemedialVariantResult(
                success=False,
                message='Нет доступных заданий для работы над ошибками.',
        )

        tasks = self.task_repo.get_by_ids(task_ids)
        student = self.student_repo.get_student(request.student_id)
        if student is None:
            return CreateStudentRemedialVariantResult(
                success=False,
                message='Ученик не найден.',
            )
        student_name = student.short_name
        work_name = f'Работа над ошибками — {student_name}'
        plan = build_remedial_variant_creation_plan(
            task_ids=task_ids,
            tasks=tasks,
            number=1,
            work_name=work_name,
        )
        if not plan.tasks:
            return CreateStudentRemedialVariantResult(
                success=False,
                message='Нет доступных заданий для работы над ошибками.',
            )

        total_score = plan.max_score_snapshot
        variant_id = self.work_repo.create_variant_from_plan(
            CreateVariantParams(
                work_id=None,
                student_id=request.student_id,
                plan=plan,
                variant_type='remedial',
            )
        )

        return CreateStudentRemedialVariantResult(
            success=True,
            variant_id=variant_id,
            task_count=len(plan.tasks),
            total_score=total_score,
            message=(
                f'Создан вариант «Работа над ошибками» для {student_name}: '
                f'{len(plan.tasks)} заданий, макс. балл: {total_score}'
            ),
        )
