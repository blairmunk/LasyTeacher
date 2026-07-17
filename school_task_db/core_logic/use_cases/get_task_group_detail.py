"""Build analog group detail screen data."""

from core_logic.entities.task import TaskGroupDetailData
from core_logic.interfaces.task_repo import ITaskRepository


class GetTaskGroupDetailUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, group_id: str) -> TaskGroupDetailData:
        group = self.task_repo.get_analog_group(group_id)
        if group is None:
            return TaskGroupDetailData(tasks=None)

        return TaskGroupDetailData(
            group=group,
            tasks=self.task_repo.get_tasks_for_analog_group(group_id),
        )
