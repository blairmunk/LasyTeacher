from unittest.mock import Mock, patch

from django.test import TestCase

from infrastructure.signals.task_cache import (
    invalidate_task_math_cache_on_delete,
    invalidate_task_math_cache_on_save,
)
from tasks.models import Task


class TaskMathCacheSignalTests(TestCase):
    @patch('infrastructure.signals.task_cache.task_math_status_cache')
    def test_invalidates_only_task_cache_for_non_text_update(self, cache):
        task = Mock(id='task-1')

        invalidate_task_math_cache_on_save(
            sender=Task,
            instance=task,
            created=False,
            update_fields={'answer'},
        )

        cache.invalidate_task_cache.assert_called_once_with('task-1')
        cache.invalidate_all_cache.assert_not_called()

    @patch('infrastructure.signals.task_cache.task_math_status_cache')
    def test_invalidates_all_cache_when_text_may_have_changed(self, cache):
        task = Mock(id='task-1')

        invalidate_task_math_cache_on_save(
            sender=Task,
            instance=task,
            created=False,
            update_fields={'text'},
        )

        cache.invalidate_all_cache.assert_called_once_with()

    @patch('infrastructure.signals.task_cache.task_math_status_cache')
    def test_invalidates_all_cache_for_regular_save(self, cache):
        task = Mock(id='task-1')

        invalidate_task_math_cache_on_save(
            sender=Task,
            instance=task,
            created=False,
            update_fields=None,
        )

        cache.invalidate_all_cache.assert_called_once_with()

    @patch('infrastructure.signals.task_cache.task_math_status_cache')
    def test_invalidates_task_and_aggregate_cache_on_delete(self, cache):
        task = Mock(id='task-1')

        invalidate_task_math_cache_on_delete(sender=Task, instance=task)

        cache.invalidate_task_cache.assert_called_once_with('task-1')
        cache.invalidate_all_cache.assert_called_once_with()
