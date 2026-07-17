"""Task import service interface."""

from abc import ABC, abstractmethod

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportPreviewResult,
    TaskImportRequest,
    TaskImportResult,
)


class ITaskImportService(ABC):
    @abstractmethod
    def preview_import(
        self,
        request: TaskImportPreviewRequest,
    ) -> TaskImportPreviewResult:
        """Run task import dry-run preview and return preview data."""

    @abstractmethod
    def execute_import(self, request: TaskImportRequest) -> TaskImportResult:
        """Execute task import and return import result."""
