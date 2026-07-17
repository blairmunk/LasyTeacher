"""Task import service interface."""

from abc import ABC, abstractmethod

from core_logic.entities.task_import import TaskImportRequest, TaskImportResult


class ITaskImportService(ABC):
    @abstractmethod
    def execute_import(self, request: TaskImportRequest) -> TaskImportResult:
        """Execute task import and return import result."""
