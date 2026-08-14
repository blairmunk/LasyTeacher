"""Refresh cached math status for tasks."""

from core_logic.entities.task import MathCacheRefreshResult
from core_logic.interfaces.task_math_status_cache import ITaskMathStatusCache


class RefreshTaskMathCacheUseCase:
    def __init__(self, math_status_cache: ITaskMathStatusCache):
        self.math_status_cache = math_status_cache

    def execute(self) -> MathCacheRefreshResult:
        stats = self.math_status_cache.refresh_cache()
        return MathCacheRefreshResult(
            status='refreshed',
            with_math_count=len(stats.with_math),
            with_errors_count=len(stats.with_errors),
            with_warnings_count=len(stats.with_warnings),
            message='Кэш успешно обновлен',
        )
