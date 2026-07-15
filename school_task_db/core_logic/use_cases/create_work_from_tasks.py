"""Create a work and first variant from selected tasks."""

from dataclasses import dataclass
from typing import List

from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.interfaces.work_repo import (
    CreateWorkWithVariantFromTasksParams,
    IWorkRepository,
)


@dataclass(frozen=True)
class CreateWorkFromTasksRequest:
    task_ids: List[str]
    work_name: str
    work_type: str = 'test'


@dataclass(frozen=True)
class CreateWorkFromTasksResult:
    status: str
    work_id: str = ''
    variant_id: str = ''
    tasks_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'created'


class CreateWorkFromTasksUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        work_repo: IWorkRepository,
    ):
        self.task_repo = task_repo
        self.work_repo = work_repo

    def execute(
        self,
        request: CreateWorkFromTasksRequest,
    ) -> CreateWorkFromTasksResult:
        task_ids = [str(task_id) for task_id in request.task_ids if task_id]
        if not task_ids:
            return CreateWorkFromTasksResult(
                status='empty_tasks',
                message='Не выбрано ни одного задания',
            )

        work_name = request.work_name.strip()
        if not work_name:
            return CreateWorkFromTasksResult(
                status='empty_name',
                message='Название работы не указано',
            )

        if self.task_repo.count_existing_task_ids(set(task_ids)) == 0:
            return CreateWorkFromTasksResult(
                status='missing_tasks',
                message='Задания не найдены',
            )

        created = self.work_repo.create_work_with_variant_from_tasks(
            CreateWorkWithVariantFromTasksParams(
                name=work_name,
                work_type=request.work_type or 'test',
                task_ids=task_ids,
            )
        )

        if created.tasks_count == 0:
            return CreateWorkFromTasksResult(
                status='missing_tasks',
                message='Задания не найдены',
            )

        return CreateWorkFromTasksResult(
            status='created',
            work_id=created.work_id,
            variant_id=created.variant_id,
            tasks_count=created.tasks_count,
            message=f'Создана работа «{work_name}» с {created.tasks_count} заданиями',
        )
