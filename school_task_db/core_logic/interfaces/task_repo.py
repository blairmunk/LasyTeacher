"""Task repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Set

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
    def get_analog_group_name(self, group_id: str) -> Optional[str]:
        """Return an analog-group name, or None when it does not exist."""

    @abstractmethod
    def add_tasks_to_group(self, group_id: str, task_ids: List[str]) -> int:
        """Add tasks to an analog group and return created membership count."""

    @abstractmethod
    def remove_task_from_group(self, group_id: str, task_id: str) -> int:
        """Remove one task from an analog group and return deleted row count."""

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
