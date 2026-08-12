"""Create and update tasks."""

from typing import List

from core_logic.entities.task import (
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskSaveParams,
    TaskSaveResult,
)
from core_logic.interfaces.task_taxonomy_repo import ITaskTaxonomyRepository
from core_logic.interfaces.task_command_repo import ITaskCommandRepository
from core_logic.interfaces.task_classification_repo import (
    ITaskClassificationRepository,
)
from core_logic.interfaces.task_image_command_repo import (
    ITaskImageCommandRepository,
)
from core_logic.value_objects.task_validation import (
    validate_task_topic_selection,
)


def _validate_task_params(
    params: TaskSaveParams,
    task_catalog_repo: ITaskTaxonomyRepository,
    classification_repo: ITaskClassificationRepository,
) -> tuple[str, ...]:
    subtopic_topic_id = None
    if params.subtopic_id:
        subtopic_topic_id = task_catalog_repo.get_subtopic_topic_id(
            params.subtopic_id,
        )
    errors = validate_task_topic_selection(
        topic_id=params.topic_id,
        subtopic_id=params.subtopic_id,
        subtopic_topic_id=subtopic_topic_id,
    )
    if errors:
        return errors
    return classification_repo.get_classification_errors(
        topic_id=params.topic_id,
        content_entry_ids=params.content_entry_ids,
        requirement_ids=params.requirement_ids,
    )


class CreateTaskUseCase:
    def __init__(
        self,
        task_repo: ITaskCommandRepository,
        task_catalog_repo: ITaskTaxonomyRepository,
        classification_repo: ITaskClassificationRepository,
    ):
        self.task_repo = task_repo
        self.task_catalog_repo = task_catalog_repo
        self.classification_repo = classification_repo

    def execute(self, params: TaskSaveParams) -> TaskSaveResult:
        errors = _validate_task_params(
            params,
            self.task_catalog_repo,
            self.classification_repo,
        )
        if errors:
            return TaskSaveResult(status='invalid', errors=errors)
        return self.task_repo.create_task(params)


class UpdateTaskUseCase:
    def __init__(
        self,
        task_repo: ITaskCommandRepository,
        task_catalog_repo: ITaskTaxonomyRepository,
        classification_repo: ITaskClassificationRepository,
    ):
        self.task_repo = task_repo
        self.task_catalog_repo = task_catalog_repo
        self.classification_repo = classification_repo

    def execute(self, params: TaskSaveParams) -> TaskSaveResult:
        errors = _validate_task_params(
            params,
            self.task_catalog_repo,
            self.classification_repo,
        )
        if errors:
            return TaskSaveResult(status='invalid', errors=errors)
        return self.task_repo.update_task(params)


class SaveTaskImagesUseCase:
    def __init__(self, task_repo: ITaskImageCommandRepository):
        self.task_repo = task_repo

    def execute(
        self,
        task_id: str,
        images: List[TaskImageSaveParams],
    ) -> TaskImagesSaveResult:
        return self.task_repo.save_task_images(task_id=task_id, images=images)
