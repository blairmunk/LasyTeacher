"""Create and update tasks."""

from typing import List

from core_logic.entities.task import (
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskSaveParams,
    TaskSaveResult,
)
from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.value_objects.task_validation import (
    validate_task_topic_selection,
)


def _validate_task_params(
    params: TaskSaveParams,
    task_repo: ITaskRepository,
) -> tuple[str, ...]:
    subtopic_topic_id = None
    if params.subtopic_id:
        subtopic_topic_id = task_repo.get_subtopic_topic_id(
            params.subtopic_id,
        )
    return validate_task_topic_selection(
        topic_id=params.topic_id,
        subtopic_id=params.subtopic_id,
        subtopic_topic_id=subtopic_topic_id,
    )


class CreateTaskUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, params: TaskSaveParams) -> TaskSaveResult:
        errors = _validate_task_params(params, self.task_repo)
        if errors:
            return TaskSaveResult(status='invalid', errors=errors)
        return self.task_repo.create_task(params)


class UpdateTaskUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, params: TaskSaveParams) -> TaskSaveResult:
        errors = _validate_task_params(params, self.task_repo)
        if errors:
            return TaskSaveResult(status='invalid', errors=errors)
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
