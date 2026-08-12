"""Command persistence port for the task lifecycle."""

from abc import ABC, abstractmethod


class ITaskLifecycleCommandRepository(ABC):
    @abstractmethod
    def delete_task(self, task_id: str) -> int:
        """Delete one task and return deleted object count."""
