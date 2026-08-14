"""Build analog group detail screen data."""

from core_logic.entities.task import TaskGroupDetailData
from core_logic.interfaces.task_group_catalog_repo import (
    ITaskGroupCatalogRepository,
)


class GetTaskGroupDetailUseCase:
    def __init__(self, task_group_repo: ITaskGroupCatalogRepository):
        self.task_group_repo = task_group_repo

    def execute(self, group_id: str) -> TaskGroupDetailData:
        group = self.task_group_repo.get_analog_group_detail(group_id)
        if group is None:
            return TaskGroupDetailData()

        return TaskGroupDetailData(
            group=group,
            tasks=self.task_group_repo.get_task_group_detail_tasks(group_id),
        )
