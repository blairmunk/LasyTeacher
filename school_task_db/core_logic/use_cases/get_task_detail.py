"""Build task detail screen data."""

from core_logic.entities.task import TaskDetailData
from core_logic.interfaces.task_read_repo import ITaskReadRepository


class GetTaskDetailUseCase:
    def __init__(self, task_repo: ITaskReadRepository):
        self.task_repo = task_repo

    def execute(self, task_id: str) -> TaskDetailData:
        task = self.task_repo.get_task(task_id)
        if task is None:
            return TaskDetailData()

        return TaskDetailData(
            task=task,
            task_groups=self.task_repo.get_task_detail_groups(task_id),
        )
