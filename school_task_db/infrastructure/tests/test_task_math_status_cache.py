from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from curriculum.models import Topic
from infrastructure.services.task_math_status_cache import (
    DjangoTaskMathStatusCache,
)
from tasks.models import Task


class DjangoTaskMathStatusCacheTests(TestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch(
        'infrastructure.services.task_math_status_cache.formula_processor'
    )
    def test_reuses_cached_status_for_single_task(self, formula_processor):
        formula_processor.has_math.return_value = True
        formula_processor.process_text_safe.return_value = {
            'has_errors': True,
            'has_warnings': False,
            'errors': ['invalid formula'],
            'warnings': [],
        }
        task = SimpleNamespace(id='task-1', text='$x$', updated_at=None)

        first = DjangoTaskMathStatusCache.get_task_math_status(task)
        second = DjangoTaskMathStatusCache.get_task_math_status(task)

        self.assertEqual(first, second)
        self.assertTrue(first['has_math'])
        self.assertEqual(first['error_count'], 1)
        formula_processor.has_math.assert_called_once_with('$x$')
        formula_processor.process_text_safe.assert_called_once_with('$x$')

    @patch(
        'infrastructure.services.task_math_status_cache.formula_processor'
    )
    def test_builds_aggregate_status_from_tasks(self, formula_processor):
        topic = Topic.objects.create(
            name='Механика',
            subject='Физика',
            section='Кинематика',
            grade_level=9,
        )
        plain_task = self._create_task(topic, 'Текст без формулы')
        formula_task = self._create_task(topic, 'Скорость $v = s / t$')
        formula_processor.has_math.side_effect = lambda text: '$' in text
        formula_processor.process_text_safe.return_value = {
            'has_errors': False,
            'has_warnings': True,
            'errors': [],
            'warnings': ['check delimiter'],
        }

        result = DjangoTaskMathStatusCache.get_all_tasks_math_status(
            force_refresh=True,
        )

        self.assertNotIn(plain_task.id, result['with_math'])
        self.assertIn(formula_task.id, result['with_math'])
        self.assertIn(formula_task.id, result['with_warnings'])
        self.assertFalse(result['with_errors'])

    def test_invalidates_single_and_aggregate_cache_separately(self):
        task_key = DjangoTaskMathStatusCache.get_task_cache_key('task-1')
        cache.set(task_key, {'has_math': True})
        cache.set(DjangoTaskMathStatusCache.CACHE_KEY_ALL_MATH, {'cached': True})

        DjangoTaskMathStatusCache.invalidate_task_cache('task-1')

        self.assertIsNone(cache.get(task_key))
        self.assertIsNotNone(
            cache.get(DjangoTaskMathStatusCache.CACHE_KEY_ALL_MATH)
        )

        DjangoTaskMathStatusCache.invalidate_all_cache()

        self.assertIsNone(
            cache.get(DjangoTaskMathStatusCache.CACHE_KEY_ALL_MATH)
        )

    @staticmethod
    def _create_task(topic, text):
        return Task.objects.create(
            text=text,
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
