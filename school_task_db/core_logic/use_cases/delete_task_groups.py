"""Delete selected analog task groups."""

from dataclasses import dataclass

from core_logic.interfaces.task_group_management_repo import (
    ITaskGroupManagementRepository,
)


@dataclass(frozen=True)
class DeleteTaskGroupsRequest:
    group_ids: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, 'group_ids', tuple(self.group_ids))


@dataclass(frozen=True)
class DeleteTaskGroupsResult:
    status: str
    deleted_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'deleted'


class DeleteTaskGroupsUseCase:
    def __init__(self, task_group_repo: ITaskGroupManagementRepository):
        self.task_group_repo = task_group_repo

    def execute(self, request: DeleteTaskGroupsRequest) -> DeleteTaskGroupsResult:
        group_ids = tuple(str(group_id) for group_id in request.group_ids if group_id)
        if not group_ids:
            return DeleteTaskGroupsResult(
                status='empty_selection',
                message='Не выбрано ни одной группы',
            )

        deleted_count = self.task_group_repo.delete_groups(group_ids)
        return DeleteTaskGroupsResult(
            status='deleted',
            deleted_count=deleted_count,
            message=f'Удалено {deleted_count} групп',
        )
