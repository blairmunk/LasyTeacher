"""Read port for task import history."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.core import ImportLogItem


class IImportLogRepository(ABC):
    @abstractmethod
    def get_recent_import_logs(self, limit: int) -> List[ImportLogItem]:
        """Return recent import logs."""

    @abstractmethod
    def get_import_logs(self) -> List[ImportLogItem]:
        """Return all import logs."""
