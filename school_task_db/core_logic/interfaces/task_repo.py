"""Task repository interface."""

from abc import ABC, abstractmethod
from typing import List, Set

from core_logic.entities.task import TaskEntity


class ITaskRepository(ABC):
    @abstractmethod
    def get_by_ids(self, task_ids: Set[str]) -> List[TaskEntity]:
        """Return tasks by IDs."""

    @abstractmethod
    def get_group_ids_for_tasks(self, task_ids: Set[str]) -> Set[str]:
        """Return analog-group IDs containing the given tasks."""

    @abstractmethod
    def count_existing_group_ids(self, group_ids: Set[str]) -> int:
        """Return how many analog groups from the given IDs exist."""

    @abstractmethod
    def get_first_task_difficulty_for_group(self, group_id: str) -> int:
        """Return the first task difficulty for an analog group, or 1."""

    @abstractmethod
    def delete_groups(self, group_ids: List[str]) -> int:
        """Delete analog groups by IDs and return deleted object count."""

    @abstractmethod
    def get_tasks_in_group(self, group_id: str) -> Set[str]:
        """Return all task IDs in an analog group."""

    @abstractmethod
    def get_tasks_by_difficulty(
        self,
        task_ids: Set[str],
        max_difficulty: int,
    ) -> List[TaskEntity]:
        """Return tasks from task_ids with difficulty not greater than max_difficulty."""
