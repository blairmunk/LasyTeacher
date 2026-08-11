"""Django task-group queries for remedial task selection."""

from typing import Set

from core_logic.interfaces.remedial_task_group_repo import (
    IRemedialTaskGroupRepository,
)
from task_groups.models import TaskGroup


class DjangoRemedialTaskGroupRepository(IRemedialTaskGroupRepository):
    def get_group_ids_for_tasks(self, task_ids: Set[str]) -> Set[str]:
        if not task_ids:
            return set()
        return {
            str(group_id)
            for group_id in TaskGroup.objects.filter(
                task_id__in=task_ids,
            ).values_list('group_id', flat=True)
        }

    def get_tasks_in_group(self, group_id: str) -> Set[str]:
        return {
            str(task_id)
            for task_id in TaskGroup.objects.filter(
                group_id=group_id,
            ).values_list('task_id', flat=True)
        }
