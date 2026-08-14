from unittest import TestCase

from core_logic.entities.task import TaskMathStatusSnapshot
from core_logic.use_cases.get_source_list import GetSourceListUseCase
from core_logic.use_cases.refresh_task_math_cache import (
    RefreshTaskMathCacheUseCase,
)


class FakeSourceRepository:
    def __init__(self):
        self.sources_requested = False

    def get_source_list_sources(self):
        self.sources_requested = True
        return ['source-1']


class FakeTaskMathStatusCache:
    def __init__(self):
        self.refreshed = False

    def refresh_cache(self):
        self.refreshed = True
        return TaskMathStatusSnapshot(
            with_math={'task-1', 'task-2'},
            with_errors={'task-2'},
        )


class SourceListAndMathCacheUseCaseTests(TestCase):
    def test_get_source_list_returns_sources(self):
        repo = FakeSourceRepository()
        use_case = GetSourceListUseCase(source_repo=repo)

        result = use_case.execute()

        self.assertTrue(repo.sources_requested)
        self.assertEqual(result.sources, ('source-1',))

    def test_refresh_math_cache_counts_stats(self):
        cache = FakeTaskMathStatusCache()
        use_case = RefreshTaskMathCacheUseCase(math_status_cache=cache)

        result = use_case.execute()

        self.assertTrue(result.success)
        self.assertTrue(cache.refreshed)
        self.assertEqual(result.with_math_count, 2)
        self.assertEqual(result.with_errors_count, 1)
        self.assertEqual(result.with_warnings_count, 0)
