"""Repository interface for selecting tasks for work composition."""

from abc import ABC, abstractmethod
from typing import Collection, Sequence

from core_logic.entities.task import TaskEntity


class ITaskSelectionRepository(ABC):
    @abstractmethod
    def get_by_ids(self, task_ids: Sequence[str]) -> tuple[TaskEntity, ...]:
        """Return tasks in the requested ID order."""

    @abstractmethod
    def count_existing_task_ids(self, task_ids: Collection[str]) -> int:
        """Return how many tasks from the given IDs exist."""

    @abstractmethod
    def get_tasks_by_difficulty(
        self,
        task_ids: Collection[str],
        max_difficulty: int,
    ) -> tuple[TaskEntity, ...]:
        """Return suitable tasks ordered by difficulty."""
