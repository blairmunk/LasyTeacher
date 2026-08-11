"""Build data for adding tasks to an analog group."""

from dataclasses import dataclass

from core_logic.entities.task import AddTasksToGroupData
from core_logic.interfaces.task_group_catalog_repo import (
    ITaskGroupCatalogRepository,
)


@dataclass(frozen=True)
class AddTasksToGroupFormRequest:
    group_id: str
    search: str = ''


class GetAddTasksToGroupUseCase:
    def __init__(self, task_group_repo: ITaskGroupCatalogRepository):
        self.task_group_repo = task_group_repo

    def execute(self, request: AddTasksToGroupFormRequest) -> AddTasksToGroupData:
        group = self.task_group_repo.get_analog_group_detail(request.group_id)
        if group is None:
            return AddTasksToGroupData(status='not_found', search=request.search)

        return AddTasksToGroupData(
            group=group,
            available_tasks=(
                self.task_group_repo.get_available_tasks_for_analog_group(
                group_id=request.group_id,
                search=request.search,
                )
            ),
            search=request.search,
        )
