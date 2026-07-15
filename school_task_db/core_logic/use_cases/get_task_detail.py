"""Build task detail screen data."""

from core_logic.entities.task import TaskDetailData
from core_logic.interfaces.task_repo import ITaskRepository


class GetTaskDetailUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def get_queryset(self):
        return self.task_repo.get_detail_tasks()

    def execute(self, task_id: str) -> TaskDetailData:
        return TaskDetailData(
            task_groups=self.task_repo.get_task_detail_groups(task_id),
        )
