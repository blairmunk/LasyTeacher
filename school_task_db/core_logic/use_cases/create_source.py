"""Create a task source."""

from core_logic.entities.task import SourceCreateParams, SourceCreateResult
from core_logic.interfaces.task_repo import ITaskRepository


class CreateSourceUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, params: SourceCreateParams) -> SourceCreateResult:
        return self.task_repo.create_source(params)
