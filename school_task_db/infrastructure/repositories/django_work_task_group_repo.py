"""Django task-group queries used while creating a work."""

from typing import Set

from core_logic.interfaces.work_task_group_repo import IWorkTaskGroupRepository
from task_groups.models import AnalogGroup, TaskGroup


class DjangoWorkTaskGroupRepository(IWorkTaskGroupRepository):
    def count_existing_group_ids(self, group_ids: Set[str]) -> int:
        if not group_ids:
            return 0
        return AnalogGroup.objects.filter(pk__in=group_ids).count()

    def get_first_task_difficulty_for_group(self, group_id: str) -> int:
        membership = TaskGroup.objects.filter(
            group_id=group_id,
        ).select_related('task').first()
        if membership and membership.task.difficulty:
            return membership.task.difficulty
        return 1
