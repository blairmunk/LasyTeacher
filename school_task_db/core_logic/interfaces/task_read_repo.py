"""Repository interface for task read models."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.task import (
    TaskDetailGroup,
    TaskDetailTask,
    TaskListFilters,
    TaskListItem,
)


class ITaskReadRepository(ABC):
    @abstractmethod
    def get_list_tasks(self, filters: TaskListFilters) -> tuple[TaskListItem, ...]:
        """Return tasks for the task list page."""

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskDetailTask]:
        """Return one task detail read model, if it exists."""

    @abstractmethod
    def get_task_detail_groups(self, task_id: str) -> tuple[TaskDetailGroup, ...]:
        """Return analog-group read models for one task detail page."""

    @abstractmethod
    def count_tasks(self) -> int:
        """Return total task count."""

    @abstractmethod
    def count_ungrouped_tasks(self) -> int:
        """Return task count without analog groups."""
