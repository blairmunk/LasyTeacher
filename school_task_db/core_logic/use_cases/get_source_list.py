"""Build source list screen data."""

from core_logic.entities.task import SourceListData
from core_logic.interfaces.task_repo import ITaskRepository


class GetSourceListUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self) -> SourceListData:
        return SourceListData(
            sources=self.task_repo.get_source_list_sources(),
        )
