from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from core_logic.entities.task import TaskMathCacheStats, TaskMathStatusSnapshot


class ManageMathCacheCommandTests(SimpleTestCase):
    @patch(
        'tasks.management.commands.manage_math_cache.task_math_status_cache'
    )
    def test_refresh_uses_typed_snapshot(self, math_status_cache):
        math_status_cache.refresh_cache.return_value = TaskMathStatusSnapshot(
            with_math={'task-1', 'task-2'},
            with_errors={'task-2'},
            with_warnings={'task-1'},
        )
        stdout = StringIO()

        call_command(
            'manage_math_cache',
            action='refresh',
            force=True,
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn('Заданий с формулами: 2', output)
        self.assertIn('Заданий с ошибками: 1', output)
        self.assertIn('Заданий с предупреждениями: 1', output)

    @patch(
        'tasks.management.commands.manage_math_cache.task_math_status_cache'
    )
    def test_stats_uses_adapter_inventory(self, math_status_cache):
        math_status_cache.get_cache_stats.return_value = TaskMathCacheStats(
            all_status_cached=True,
            with_math_cached=True,
            with_errors_cached=True,
            total_with_math=3,
            total_with_errors=1,
        )
        math_status_cache.get_cache_inventory.return_value = {
            'total_tasks': 5,
            'sample_size': 5,
            'cached_in_sample': 4,
        }
        stdout = StringIO()

        call_command('manage_math_cache', action='stats', stdout=stdout)

        output = stdout.getvalue()
        self.assertIn('Всего заданий в базе: 5', output)
        self.assertIn('4/5', output)
        math_status_cache.get_cache_inventory.assert_called_once_with()

    @patch(
        'tasks.management.commands.manage_math_cache.task_math_status_cache'
    )
    def test_warmup_delegates_batching_to_adapter(self, math_status_cache):
        math_status_cache.warmup_cache.return_value = 7
        stdout = StringIO()

        call_command(
            'manage_math_cache',
            action='warmup',
            batch_size=25,
            stdout=stdout,
        )

        math_status_cache.warmup_cache.assert_called_once_with(batch_size=25)
        self.assertIn('Обработано 7 заданий', stdout.getvalue())
