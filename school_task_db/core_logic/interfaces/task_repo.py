"""Task repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.task import (
    TaskDetailGroup,
    TaskDetailTask,
    TaskListItem,
    TaskListFilters,
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskSaveParams,
    TaskSaveResult,
)


class ITaskRepository(ABC):
    @abstractmethod
    def get_list_tasks(self, filters: TaskListFilters) -> List[TaskListItem]:
        """Return tasks for the task list page."""

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskDetailTask]:
        """Return one task detail read model, or None when it does not exist."""

    @abstractmethod
    def create_task(self, params: TaskSaveParams) -> TaskSaveResult:
        """Create a task."""

    @abstractmethod
    def update_task(self, params: TaskSaveParams) -> TaskSaveResult:
        """Update a task, or return not_found status."""

    @abstractmethod
    def save_task_images(
        self,
        task_id: str,
        images: List[TaskImageSaveParams],
    ) -> TaskImagesSaveResult:
        """Persist task images and return change counts."""

    @abstractmethod
    def get_task_detail_groups(self, task_id: str) -> List[TaskDetailGroup]:
        """Return analog-group read models for one task detail page."""

    @abstractmethod
    def count_tasks(self) -> int:
        """Return total task count."""

    @abstractmethod
    def count_ungrouped_tasks(self) -> int:
        """Return task count without analog groups."""

    @abstractmethod
    def delete_task(self, task_id: str) -> int:
        """Delete one task and return deleted object count."""
