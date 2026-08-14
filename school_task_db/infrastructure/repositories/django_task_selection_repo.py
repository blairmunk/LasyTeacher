"""Django repository for selecting tasks for work composition."""

from typing import Collection, Sequence

from core_logic.entities.task import TaskEntity
from core_logic.interfaces.task_selection_repo import ITaskSelectionRepository
from tasks.models import Task


class DjangoTaskSelectionRepository(ITaskSelectionRepository):
    def get_by_ids(self, task_ids: Sequence[str]) -> tuple[TaskEntity, ...]:
        if not task_ids:
            return ()

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
        return tuple(
            task_map[str(task_id)]
            for task_id in task_ids
            if str(task_id) in task_map
        )

    def count_existing_task_ids(self, task_ids: Collection[str]) -> int:
        if not task_ids:
            return 0
        return Task.objects.filter(pk__in=task_ids).count()

    def get_tasks_by_difficulty(
        self,
        task_ids: Collection[str],
        max_difficulty: int,
    ) -> tuple[TaskEntity, ...]:
        if not task_ids:
            return ()

        tasks = Task.objects.filter(
            id__in=task_ids,
            difficulty__lte=max_difficulty,
        ).order_by('difficulty', 'id')
        return tuple(
            TaskEntity(
                id=str(task.id),
                text=task.text,
                difficulty=task.difficulty or 1,
                estimated_time=task.estimated_time,
            )
            for task in tasks
        )
