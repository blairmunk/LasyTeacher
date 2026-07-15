"""Mutate task membership in analog groups."""

from dataclasses import dataclass
from typing import List

from core_logic.interfaces.task_repo import ITaskRepository


@dataclass(frozen=True)
class AddTasksToGroupRequest:
    group_id: str
    task_ids: List[str]


@dataclass(frozen=True)
class AddTasksToGroupResult:
    status: str
    group_name: str = ''
    created_count: int = 0

    @property
    def success(self) -> bool:
        return self.status == 'added'


class AddTasksToGroupUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, request: AddTasksToGroupRequest) -> AddTasksToGroupResult:
        group_name = self.task_repo.get_analog_group_name(request.group_id)
        if group_name is None:
            return AddTasksToGroupResult(status='not_found')

        task_ids = [str(task_id) for task_id in request.task_ids if task_id]
        created_count = self.task_repo.add_tasks_to_group(
            group_id=request.group_id,
            task_ids=task_ids,
        )
        return AddTasksToGroupResult(
            status='added',
            group_name=group_name,
            created_count=created_count,
        )


@dataclass(frozen=True)
class RemoveTaskFromGroupRequest:
    group_id: str
    task_id: str


@dataclass(frozen=True)
class RemoveTaskFromGroupResult:
    status: str
    group_name: str = ''
    deleted_count: int = 0

    @property
    def success(self) -> bool:
        return self.status == 'removed'


class RemoveTaskFromGroupUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(
        self,
        request: RemoveTaskFromGroupRequest,
    ) -> RemoveTaskFromGroupResult:
        group_name = self.task_repo.get_analog_group_name(request.group_id)
        if group_name is None:
            return RemoveTaskFromGroupResult(status='not_found')

        deleted_count = self.task_repo.remove_task_from_group(
            group_id=request.group_id,
            task_id=request.task_id,
        )
        return RemoveTaskFromGroupResult(
            status='removed',
            group_name=group_name,
            deleted_count=deleted_count,
        )
