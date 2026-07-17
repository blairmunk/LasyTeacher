"""Core repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ICoreRepository(ABC):
    @abstractmethod
    def count_tasks(self) -> int:
        """Return task count."""

    @abstractmethod
    def count_works(self) -> int:
        """Return work count."""

    @abstractmethod
    def count_variants(self) -> int:
        """Return variant count."""

    @abstractmethod
    def count_orphan_variants(self) -> int:
        """Return variants not attached to a work."""

    @abstractmethod
    def count_students(self) -> int:
        """Return student count."""

    @abstractmethod
    def count_events(self) -> int:
        """Return event count."""

    @abstractmethod
    def count_analog_groups(self) -> int:
        """Return analog group count."""

    @abstractmethod
    def get_recent_import_logs(self, limit: int) -> Any:
        """Return recent import logs."""

    @abstractmethod
    def get_import_logs(self) -> Any:
        """Return all import logs."""

    @abstractmethod
    def search_by_uuid(self, query: str) -> Dict[str, object]:
        """Return global search results by UUID fragment."""

    @abstractmethod
    def search_by_text(self, words: List[str]) -> Dict[str, object]:
        """Return global search results by text words."""
