"""Django repository for selecting tasks for work composition."""

from typing import List, Set

from core_logic.entities.task import TaskEntity
from core_logic.interfaces.task_selection_repo import ITaskSelectionRepository
from tasks.models import Task


class DjangoTaskSelectionRepository(ITaskSelectionRepository):
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

    def count_existing_task_ids(self, task_ids: Set[str]) -> int:
        if not task_ids:
            return 0
        return Task.objects.filter(pk__in=task_ids).count()

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
