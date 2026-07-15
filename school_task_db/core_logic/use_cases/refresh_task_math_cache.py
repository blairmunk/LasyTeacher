"""Refresh cached math status for tasks."""

from core_logic.entities.task import MathCacheRefreshResult
from core_logic.interfaces.task_repo import ITaskRepository


class RefreshTaskMathCacheUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self) -> MathCacheRefreshResult:
        stats = self.task_repo.refresh_math_cache()
        return MathCacheRefreshResult(
            status='refreshed',
            with_math_count=len(stats.get('with_math', [])),
            with_errors_count=len(stats.get('with_errors', [])),
            with_warnings_count=len(stats.get('with_warnings', [])),
            message='Кэш успешно обновлен',
        )
