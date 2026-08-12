"""Command persistence port for task fields."""

from abc import ABC, abstractmethod

from core_logic.entities.task import TaskSaveParams, TaskSaveResult


class ITaskCommandRepository(ABC):
    @abstractmethod
    def create_task(self, params: TaskSaveParams) -> TaskSaveResult:
        """Create a task."""

    @abstractmethod
    def update_task(self, params: TaskSaveParams) -> TaskSaveResult:
        """Update a task, or return not_found status."""
