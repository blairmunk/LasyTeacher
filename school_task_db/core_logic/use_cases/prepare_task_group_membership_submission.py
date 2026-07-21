"""Prepare task group membership POST data."""

from dataclasses import dataclass
from typing import Mapping, Sequence

from core_logic.use_cases.change_task_group_membership import (
    AddTasksToGroupRequest,
    UpdateTaskGroupRolesRequest,
)
from core_logic.value_objects.task_print_settings import TASK_BANK_ROLE_CONTROL


@dataclass(frozen=True)
class PrepareAddTasksToGroupSubmissionRequest:
    group_id: str
    data: Mapping[str, Sequence[str]]


class PrepareAddTasksToGroupSubmissionUseCase:
    def execute(
        self,
        request: PrepareAddTasksToGroupSubmissionRequest,
    ) -> AddTasksToGroupRequest:
        return AddTasksToGroupRequest(
            group_id=request.group_id,
            task_ids=_list(request.data, 'selected_tasks'),
            bank_role=_first(request.data, 'bank_role') or TASK_BANK_ROLE_CONTROL,
        )


@dataclass(frozen=True)
class PrepareUpdateTaskGroupRolesSubmissionRequest:
    group_id: str
    data: Mapping[str, Sequence[str]]


class PrepareUpdateTaskGroupRolesSubmissionUseCase:
    def execute(
        self,
        request: PrepareUpdateTaskGroupRolesSubmissionRequest,
    ) -> UpdateTaskGroupRolesRequest:
        return UpdateTaskGroupRolesRequest(
            group_id=request.group_id,
            task_roles={
                key.removeprefix('task_role_'): _first(request.data, key)
                for key in request.data
                if key.startswith('task_role_')
            },
        )


def _list(data: Mapping[str, Sequence[str]], key: str):
    values = data.get(key)
    if not values:
        return []
    return [str(value) for value in values]


def _first(data: Mapping[str, Sequence[str]], key: str):
    values = data.get(key)
    if not values:
        return ''
    return str(values[0])
