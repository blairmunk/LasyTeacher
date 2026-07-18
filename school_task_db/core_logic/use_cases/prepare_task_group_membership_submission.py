"""Prepare task group membership POST data."""

from dataclasses import dataclass
from typing import Mapping, Sequence

from core_logic.use_cases.change_task_group_membership import (
    AddTasksToGroupRequest,
)


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
        )


def _list(data: Mapping[str, Sequence[str]], key: str):
    values = data.get(key)
    if not values:
        return []
    return [str(value) for value in values]
