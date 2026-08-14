"""Port for cached task formula diagnostics."""

from abc import ABC, abstractmethod

from core_logic.entities.task import TaskMathCacheStats, TaskMathStatusSnapshot


class ITaskMathStatusCache(ABC):
    @abstractmethod
    def get_tasks_with_math_ids(self) -> frozenset[str]:
        """Return IDs of tasks containing mathematical markup."""

    @abstractmethod
    def get_tasks_with_errors_ids(self) -> frozenset[str]:
        """Return IDs of tasks with invalid mathematical markup."""

    @abstractmethod
    def get_cache_stats(self) -> TaskMathCacheStats:
        """Return cache availability and aggregate counters."""

    @abstractmethod
    def refresh_cache(self) -> TaskMathStatusSnapshot:
        """Rebuild aggregate diagnostics and return grouped task IDs."""
