"""Create and update tasks."""

from typing import List

from core_logic.entities.task import (
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskSaveParams,
    TaskSaveResult,
)
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


class SaveTaskImagesUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(
        self,
        task_id: str,
        images: List[TaskImageSaveParams],
    ) -> TaskImagesSaveResult:
        return self.task_repo.save_task_images(task_id=task_id, images=images)
