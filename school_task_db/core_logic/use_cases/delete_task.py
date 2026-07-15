"""Delete one task."""

from dataclasses import dataclass

from core_logic.interfaces.task_repo import ITaskRepository


@dataclass(frozen=True)
class DeleteTaskRequest:
    task_id: str


@dataclass(frozen=True)
class DeleteTaskResult:
    status: str
    deleted_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'deleted'


class DeleteTaskUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, request: DeleteTaskRequest) -> DeleteTaskResult:
        if not request.task_id:
            return DeleteTaskResult(
                status='empty_task',
                message='Задание не указано',
            )

        deleted_count = self.task_repo.delete_task(request.task_id)
        return DeleteTaskResult(
            status='deleted',
            deleted_count=deleted_count,
            message='Задание успешно удалено!',
        )
