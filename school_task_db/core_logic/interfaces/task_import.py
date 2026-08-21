"""Task import execution and journaling ports."""

from abc import ABC, abstractmethod

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportRequest,
    TaskImportRunSummary,
)


class ITaskImportRunner(ABC):
    @abstractmethod
    def preview_import(
        self,
        request: TaskImportPreviewRequest,
    ) -> TaskImportRunSummary:
        """Run read-only task import analysis."""

    @abstractmethod
    def execute_import(
        self,
        request: TaskImportRequest,
    ) -> TaskImportRunSummary:
        """Execute task import and return normalized operation facts."""


class ITaskImportLogRepository(ABC):
    @abstractmethod
    def start(self, request: TaskImportRequest) -> str:
        """Create an importing log entry and return its identifier."""

    @abstractmethod
    def complete(
        self,
        log_id: str,
        summary: TaskImportRunSummary,
        duration_ms: int,
    ) -> None:
        """Persist a successful or partial import summary."""

    @abstractmethod
    def fail(self, log_id: str, error: str, duration_ms: int) -> None:
        """Persist a failed import result."""
