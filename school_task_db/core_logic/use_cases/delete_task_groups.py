"""Delete selected analog task groups."""

from dataclasses import dataclass
from typing import List

from core_logic.interfaces.task_repo import ITaskRepository


@dataclass(frozen=True)
class DeleteTaskGroupsRequest:
    group_ids: List[str]


@dataclass(frozen=True)
class DeleteTaskGroupsResult:
    status: str
    deleted_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'deleted'


class DeleteTaskGroupsUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, request: DeleteTaskGroupsRequest) -> DeleteTaskGroupsResult:
        group_ids = [str(group_id) for group_id in request.group_ids if group_id]
        if not group_ids:
            return DeleteTaskGroupsResult(
                status='empty_selection',
                message='Не выбрано ни одной группы',
            )

        deleted_count = self.task_repo.delete_groups(group_ids)
        return DeleteTaskGroupsResult(
            status='deleted',
            deleted_count=deleted_count,
            message=f'Удалено {deleted_count} групп',
        )
