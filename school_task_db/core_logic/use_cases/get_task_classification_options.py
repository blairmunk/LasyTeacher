"""Build explicit classification options for the task form."""

from core_logic.entities.task import TaskClassificationOptions
from core_logic.interfaces.task_classification_repo import (
    ITaskClassificationRepository,
)


class GetTaskClassificationOptionsUseCase:
    def __init__(
        self,
        classification_repo: ITaskClassificationRepository,
    ):
        self.classification_repo = classification_repo

    def execute(self, topic_id: str) -> TaskClassificationOptions:
        if not topic_id:
            return TaskClassificationOptions(
                content_entries=[],
                requirements=[],
            )
        return self.classification_repo.get_classification_options(topic_id)
