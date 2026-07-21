"""Mutate task membership in analog groups."""

from dataclasses import dataclass
from typing import Dict, List

from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.value_objects.variant_print_plan import (
    TASK_BANK_ROLE_CONTROL,
    validate_task_specific_bank_role,
)


@dataclass(frozen=True)
class AddTasksToGroupRequest:
    group_id: str
    task_ids: List[str]
    bank_role: str = TASK_BANK_ROLE_CONTROL


@dataclass(frozen=True)
class AddTasksToGroupResult:
    status: str
    group_name: str = ''
    created_count: int = 0
    errors: tuple[str, ...] = ()

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
        try:
            validate_task_specific_bank_role(request.bank_role)
        except ValueError as error:
            return AddTasksToGroupResult(
                status='invalid',
                group_name=group_name,
                errors=(str(error),),
            )
        created_count = self.task_repo.add_tasks_to_group(
            group_id=request.group_id,
            task_ids=task_ids,
            bank_role=request.bank_role,
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


@dataclass(frozen=True)
class UpdateTaskGroupRolesRequest:
    group_id: str
    task_roles: Dict[str, str]


@dataclass(frozen=True)
class UpdateTaskGroupRolesResult:
    status: str
    group_name: str = ''
    updated_count: int = 0
    errors: tuple[str, ...] = ()

    @property
    def success(self) -> bool:
        return self.status == 'updated'


class UpdateTaskGroupRolesUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(
        self,
        request: UpdateTaskGroupRolesRequest,
    ) -> UpdateTaskGroupRolesResult:
        group_name = self.task_repo.get_analog_group_name(request.group_id)
        if group_name is None:
            return UpdateTaskGroupRolesResult(status='not_found')

        task_roles = {
            str(task_id): str(bank_role)
            for task_id, bank_role in request.task_roles.items()
            if task_id
        }
        errors = []
        for bank_role in task_roles.values():
            try:
                validate_task_specific_bank_role(bank_role)
            except ValueError as error:
                errors.append(str(error))

        if errors:
            return UpdateTaskGroupRolesResult(
                status='invalid',
                group_name=group_name,
                errors=tuple(errors),
            )

        updated_count = self.task_repo.update_task_group_roles(
            group_id=request.group_id,
            task_roles=task_roles,
        )
        return UpdateTaskGroupRolesResult(
            status='updated',
            group_name=group_name,
            updated_count=updated_count,
        )
