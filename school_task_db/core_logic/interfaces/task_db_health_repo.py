"""Port for task database diagnostics."""

from abc import ABC, abstractmethod

from core_logic.entities.report import TaskDBHealthSource


class ITaskDBHealthRepository(ABC):
    @abstractmethod
    def get_task_db_health_source(self) -> TaskDBHealthSource:
        """Return normalized facts for task database diagnostics."""
