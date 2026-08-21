"""Task import execution, persistence, and journaling ports."""

from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportPreviewFacts,
    TaskImportPreviewLookup,
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


class ITaskImportWriteSession(ABC):
    """Stateful persistence session scoped to one task-bank import."""

    @abstractmethod
    def import_sources(self, records: Sequence[Mapping[str, Any]]) -> None:
        """Persist source records."""

    @abstractmethod
    def import_groups(self, records: Sequence[Mapping[str, Any]]) -> None:
        """Persist analog-group records."""

    @abstractmethod
    def import_topics(self, records: Sequence[Mapping[str, Any]]) -> None:
        """Persist topic and subtopic records."""

    @abstractmethod
    def import_tasks(self, records: Sequence[Mapping[str, Any]]) -> None:
        """Persist task records and their direct references."""

    @abstractmethod
    def import_task_group_relations(
        self,
        records: Sequence[Mapping[str, Any]],
    ) -> None:
        """Persist task-to-group relations after both sides exist."""

    @abstractmethod
    def import_images(self, records: Sequence[Mapping[str, Any]]) -> None:
        """Persist task image records."""

    @abstractmethod
    def summary(self) -> TaskImportRunSummary:
        """Return facts accumulated by this import session."""


class ITaskImportWriteSessionFactory(ABC):
    """Create isolated persistence state for one task import."""

    @abstractmethod
    def create(
        self,
        *,
        mode: str,
        create_missing: bool,
    ) -> ITaskImportWriteSession:
        """Return a fresh write session configured for the request."""


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


class ITaskImportPreviewRepository(ABC):
    @abstractmethod
    def get_facts(
        self,
        lookup: TaskImportPreviewLookup,
    ) -> TaskImportPreviewFacts:
        """Return existing database identities needed for a dry-run."""
