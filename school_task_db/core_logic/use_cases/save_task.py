"""Create and update tasks."""

from core_logic.entities.task import TaskSaveParams, TaskSaveResult
from core_logic.interfaces.task_repo import ITaskRepository


class CreateTaskUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, params: TaskSaveParams) -> TaskSaveResult:
        return self.task_repo.create_task(params)


class UpdateTaskUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, params: TaskSaveParams) -> TaskSaveResult:
        return self.task_repo.update_task(params)
