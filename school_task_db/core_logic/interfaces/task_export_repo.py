"""Task export source repository interface."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.task import TaskExportFilters, TaskExportTaskSource


class ITaskExportRepository(ABC):
    @abstractmethod
    def get_task_export_sources(
        self,
        filters: TaskExportFilters,
    ) -> List[TaskExportTaskSource]:
        """Return normalized task records for portable export."""
