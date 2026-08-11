"""Task-group query port used by remedial task selection."""

from abc import ABC, abstractmethod
from typing import Set


class IRemedialTaskGroupRepository(ABC):
    @abstractmethod
    def get_group_ids_for_tasks(self, task_ids: Set[str]) -> Set[str]:
        """Return analog-group IDs containing the given tasks."""

    @abstractmethod
    def get_tasks_in_group(self, group_id: str) -> Set[str]:
        """Return all task IDs in an analog group."""
