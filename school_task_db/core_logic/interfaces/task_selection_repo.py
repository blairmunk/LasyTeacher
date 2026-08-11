"""Repository interface for selecting tasks for work composition."""

from abc import ABC, abstractmethod
from typing import List, Set

from core_logic.entities.task import TaskEntity


class ITaskSelectionRepository(ABC):
    @abstractmethod
    def get_by_ids(self, task_ids: Set[str]) -> List[TaskEntity]:
        """Return tasks by IDs."""

    @abstractmethod
    def count_existing_task_ids(self, task_ids: Set[str]) -> int:
        """Return how many tasks from the given IDs exist."""

    @abstractmethod
    def get_tasks_by_difficulty(
        self,
        task_ids: Set[str],
        max_difficulty: int,
    ) -> List[TaskEntity]:
        """Return suitable tasks ordered by difficulty."""
