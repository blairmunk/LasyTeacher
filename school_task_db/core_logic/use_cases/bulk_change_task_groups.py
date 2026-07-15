"""Bulk task-group operations for selected tasks."""

from dataclasses import dataclass
from typing import List

from core_logic.interfaces.task_repo import ITaskRepository


@dataclass(frozen=True)
class BulkCreateGroupFromTasksRequest:
    task_ids: List[str]
    group_name: str


@dataclass(frozen=True)
class BulkCreateGroupFromTasksResult:
    status: str
    group_id: str = ''
    group_name: str = ''
    added_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'created'


class BulkCreateGroupFromTasksUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(
        self,
        request: BulkCreateGroupFromTasksRequest,
    ) -> BulkCreateGroupFromTasksResult:
        task_ids = [str(task_id) for task_id in request.task_ids if task_id]
        if not task_ids:
            return BulkCreateGroupFromTasksResult(
                status='empty_tasks',
                message='Не выбрано ни одного задания',
            )

        group_name = request.group_name.strip()
        if not group_name:
            return BulkCreateGroupFromTasksResult(
                status='empty_name',
                message='Название группы не указано',
            )
        if self.task_repo.analog_group_name_exists(group_name):
            return BulkCreateGroupFromTasksResult(
                status='duplicate_name',
                message='Группа с таким названием уже существует',
            )
        if self.task_repo.count_existing_task_ids(set(task_ids)) == 0:
            return BulkCreateGroupFromTasksResult(
                status='missing_tasks',
                message='Задания не найдены',
            )

        group_id = self.task_repo.create_analog_group(
            name=group_name,
            description='Создана из выбранных заданий',
        )
        added_count = self.task_repo.add_tasks_to_group(group_id, task_ids)
        return BulkCreateGroupFromTasksResult(
            status='created',
            group_id=group_id,
            group_name=group_name,
            added_count=added_count,
            message=f'Создана группа «{group_name}» с {added_count} заданиями',
        )


@dataclass(frozen=True)
class BulkAddTasksToGroupRequest:
    task_ids: List[str]
    group_id: str


@dataclass(frozen=True)
class BulkAddTasksToGroupResult:
    status: str
    group_name: str = ''
    added_count: int = 0
    skipped_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'added'


class BulkAddTasksToGroupUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, request: BulkAddTasksToGroupRequest) -> BulkAddTasksToGroupResult:
        task_ids = [str(task_id) for task_id in request.task_ids if task_id]
        if not task_ids:
            return BulkAddTasksToGroupResult(
                status='empty_tasks',
                message='Не выбрано ни одного задания',
            )
        if not request.group_id:
            return BulkAddTasksToGroupResult(
                status='empty_group',
                message='Группа не указана',
            )

        group_name = self.task_repo.get_analog_group_name(request.group_id)
        if group_name is None:
            return BulkAddTasksToGroupResult(
                status='missing_group',
                message='Группа не найдена',
            )

        existing_count = self.task_repo.count_existing_task_ids(set(task_ids))
        added_count = self.task_repo.add_tasks_to_group(request.group_id, task_ids)
        skipped_count = max(0, existing_count - added_count)
        message = f'Добавлено {added_count} заданий в «{group_name}»'
        if skipped_count:
            message += f' (пропущено {skipped_count} — уже в группе)'

        return BulkAddTasksToGroupResult(
            status='added',
            group_name=group_name,
            added_count=added_count,
            skipped_count=skipped_count,
            message=message,
        )


@dataclass(frozen=True)
class BulkRemoveTasksFromGroupsRequest:
    task_ids: List[str]


@dataclass(frozen=True)
class BulkRemoveTasksFromGroupsResult:
    status: str
    removed_count: int = 0
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'removed'


class BulkRemoveTasksFromGroupsUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(
        self,
        request: BulkRemoveTasksFromGroupsRequest,
    ) -> BulkRemoveTasksFromGroupsResult:
        task_ids = [str(task_id) for task_id in request.task_ids if task_id]
        if not task_ids:
            return BulkRemoveTasksFromGroupsResult(
                status='empty_tasks',
                message='Не выбрано ни одного задания',
            )

        removed_count = self.task_repo.remove_tasks_from_all_groups(task_ids)
        return BulkRemoveTasksFromGroupsResult(
            status='removed',
            removed_count=removed_count,
            message=f'Удалено {removed_count} связей с группами',
        )
