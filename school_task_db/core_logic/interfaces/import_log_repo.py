"""Read port for task import history."""

from abc import ABC, abstractmethod
from typing import Any


class IImportLogRepository(ABC):
    @abstractmethod
    def get_recent_import_logs(self, limit: int) -> Any:
        """Return recent import logs."""

    @abstractmethod
    def get_import_logs(self) -> Any:
        """Return all import logs."""
