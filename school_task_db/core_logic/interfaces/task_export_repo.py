"""Task export source repository interface."""

from abc import ABC, abstractmethod
from core_logic.entities.task import TaskExportFilters, TaskExportTaskSource


class ITaskExportRepository(ABC):
    @abstractmethod
    def get_task_export_sources(
        self,
        filters: TaskExportFilters,
    ) -> tuple[TaskExportTaskSource, ...]:
        """Return normalized task records for portable export."""
