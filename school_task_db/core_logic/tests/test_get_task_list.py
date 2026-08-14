from datetime import datetime
from unittest import TestCase

from core_logic.entities.task import (
    SelectOption,
    TaskListFilters,
    TaskListItem,
    TaskMathCacheStats,
)
from core_logic.use_cases.get_task_list import GetTaskListUseCase


class FakeTaskRepository:
    def __init__(self):
        self.filters = None

    def get_list_tasks(self, filters):
        self.filters = filters
        return (
            TaskListItem(
                pk='task-1',
                text='Задание',
                topic_name='Динамика',
                task_type_display='Расчётная задача',
                difficulty_display='Базовый',
                display_id='task-1',
                created_at=datetime(2026, 8, 14),
            ),
        )

    def get_list_topics(self):
        return (SelectOption('topic-1', 'Динамика'),)

    def get_list_analog_groups(self):
        return (SelectOption('group-1', 'Скорость'),)

    def get_list_sources(self):
        return (SelectOption('source-1', 'Сборник'),)

    def get_subtopics_for_topic(self, topic_id):
        return (
            (SelectOption(f'subtopic-for-{topic_id}', 'Подтема'),)
            if topic_id
            else ()
        )

    def get_task_type_choices(self):
        return (('computational', 'Расчётная задача'),)

    def count_tasks(self):
        return 7

    def count_ungrouped_tasks(self):
        return 2


class FakeTaskMathStatusCache:
    def __init__(self):
        self.stats_requested = False

    def get_cache_stats(self):
        self.stats_requested = True
        return TaskMathCacheStats(
            all_status_cached=True,
            with_math_cached=True,
            with_errors_cached=True,
            total_with_math=7,
            total_with_errors=1,
        )


class GetTaskListUseCaseTests(TestCase):
    def test_execute_builds_task_list_data(self):
        repo = FakeTaskRepository()
        cache = FakeTaskMathStatusCache()
        use_case = GetTaskListUseCase(
            task_repo=repo,
            task_catalog_repo=repo,
            task_group_repo=repo,
            math_status_cache=cache,
        )
        filters = TaskListFilters(topic_id='topic-1', search='сила')

        data = use_case.execute(filters, include_cache_stats=True)

        self.assertEqual(repo.filters, filters)
        self.assertEqual(data.tasks[0].pk, 'task-1')
        self.assertEqual(data.topics[0].pk, 'topic-1')
        self.assertEqual(data.analog_groups[0].pk, 'group-1')
        self.assertEqual(data.sources[0].pk, 'source-1')
        self.assertEqual(data.subtopics[0].pk, 'subtopic-for-topic-1')
        self.assertEqual(
            data.task_types,
            (('computational', 'Расчётная задача'),),
        )
        self.assertEqual(data.grade_choices[0], (7, '7 класс'))
        self.assertEqual(data.total_tasks, 7)
        self.assertEqual(data.ungrouped_count, 2)
        self.assertEqual(data.cache_stats.total_with_math, 7)
        self.assertTrue(cache.stats_requested)

    def test_execute_skips_cache_stats_for_non_staff_context(self):
        repo = FakeTaskRepository()
        cache = FakeTaskMathStatusCache()
        use_case = GetTaskListUseCase(
            task_repo=repo,
            task_catalog_repo=repo,
            task_group_repo=repo,
            math_status_cache=cache,
        )

        data = use_case.execute(TaskListFilters())

        self.assertIsNone(data.cache_stats)
        self.assertFalse(cache.stats_requested)
