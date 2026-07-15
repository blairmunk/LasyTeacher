"""Django implementation of the task repository."""

from typing import List, Set

from core_logic.entities.task import TaskEntity
from core_logic.interfaces.task_repo import ITaskRepository
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task


class DjangoTaskRepository(ITaskRepository):
    def get_by_ids(self, task_ids: Set[str]) -> List[TaskEntity]:
        if not task_ids:
            return []

        tasks = Task.objects.filter(id__in=task_ids)
        task_map = {
            str(task.id): TaskEntity(
                id=str(task.id),
                text=task.text,
                difficulty=task.difficulty or 1,
                estimated_time=task.estimated_time,
            )
            for task in tasks
        }
        return [task_map[task_id] for task_id in task_ids if task_id in task_map]

    def get_group_ids_for_tasks(self, task_ids: Set[str]) -> Set[str]:
        if not task_ids:
            return set()

        return {
            str(group_id)
            for group_id in TaskGroup.objects.filter(
                task_id__in=task_ids
            ).values_list('group_id', flat=True)
        }

    def count_existing_group_ids(self, group_ids: Set[str]) -> int:
        if not group_ids:
            return 0

        return AnalogGroup.objects.filter(pk__in=group_ids).count()

    def get_first_task_difficulty_for_group(self, group_id: str) -> int:
        task_group = TaskGroup.objects.filter(
            group_id=group_id,
        ).select_related('task').first()
        if task_group and task_group.task.difficulty:
            return task_group.task.difficulty
        return 1

    def get_analog_group_name(self, group_id: str):
        return AnalogGroup.objects.filter(pk=group_id).values_list(
            'name',
            flat=True,
        ).first()

    def add_tasks_to_group(self, group_id: str, task_ids: List[str]) -> int:
        created_count = 0
        for task in Task.objects.filter(pk__in=task_ids):
            _, created = TaskGroup.objects.get_or_create(
                task=task,
                group_id=group_id,
            )
            if created:
                created_count += 1
        return created_count

    def remove_task_from_group(self, group_id: str, task_id: str) -> int:
        return TaskGroup.objects.filter(
            group_id=group_id,
            task_id=task_id,
        ).delete()[0]

    def delete_groups(self, group_ids: List[str]) -> int:
        if not group_ids:
            return 0

        groups = AnalogGroup.objects.filter(pk__in=group_ids)
        deleted_count = groups.count()
        groups.delete()
        return deleted_count

    def get_tasks_in_group(self, group_id: str) -> Set[str]:
        return {
            str(task_id)
            for task_id in TaskGroup.objects.filter(
                group_id=group_id
            ).values_list('task_id', flat=True)
        }

    def get_tasks_by_difficulty(
        self,
        task_ids: Set[str],
        max_difficulty: int,
    ) -> List[TaskEntity]:
        if not task_ids:
            return []

        tasks = Task.objects.filter(
            id__in=task_ids,
            difficulty__lte=max_difficulty,
        ).order_by('difficulty', 'id')

        return [
            TaskEntity(
                id=str(task.id),
                text=task.text,
                difficulty=task.difficulty or 1,
                estimated_time=task.estimated_time,
            )
            for task in tasks
        ]
