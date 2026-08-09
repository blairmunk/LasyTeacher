"""Port for cached task formula diagnostics."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Set


class ITaskMathStatusCache(ABC):
    @abstractmethod
    def get_tasks_with_math_ids(self) -> Set[Any]:
        """Return IDs of tasks containing mathematical markup."""

    @abstractmethod
    def get_tasks_with_errors_ids(self) -> Set[Any]:
        """Return IDs of tasks with invalid mathematical markup."""

    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache availability and aggregate counters."""

    @abstractmethod
    def refresh_cache(self) -> Dict[str, Set[Any]]:
        """Rebuild aggregate diagnostics and return grouped task IDs."""
