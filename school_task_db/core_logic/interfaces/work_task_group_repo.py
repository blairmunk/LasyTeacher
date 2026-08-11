"""Task-group query port used while creating a work."""

from abc import ABC, abstractmethod
from typing import Set


class IWorkTaskGroupRepository(ABC):
    @abstractmethod
    def count_existing_group_ids(self, group_ids: Set[str]) -> int:
        """Return how many selected analog groups exist."""

    @abstractmethod
    def get_first_task_difficulty_for_group(self, group_id: str) -> int:
        """Return first task difficulty for a group, or 1."""
