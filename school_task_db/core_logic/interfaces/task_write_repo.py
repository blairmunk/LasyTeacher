"""Repository interface for task write operations."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.task import (
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskSaveParams,
    TaskSaveResult,
)


class ITaskWriteRepository(ABC):
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
    def delete_task(self, task_id: str) -> int:
        """Delete one task and return deleted object count."""
