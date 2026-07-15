from unittest import TestCase

from core_logic.entities.task import TaskListFilters
from core_logic.use_cases.get_task_list import GetTaskListUseCase


class FakeTaskRepository:
    def __init__(self):
        self.filters = None
        self.cache_stats_requested = False

    def get_list_tasks(self, filters):
        self.filters = filters
        return ['task-1']

    def get_list_topics(self):
        return ['topic-1']

    def get_list_analog_groups(self):
        return ['group-1']

    def get_list_sources(self):
        return ['source-1']

    def get_subtopics_for_topic(self, topic_id):
        return [f'subtopic-for-{topic_id}'] if topic_id else []

    def get_task_type_choices(self):
        return [('computational', 'Расчётная задача')]

    def count_tasks(self):
        return 7

    def count_ungrouped_tasks(self):
        return 2

    def get_math_cache_stats(self):
        self.cache_stats_requested = True
        return {'total': 7}


class GetTaskListUseCaseTests(TestCase):
    def test_execute_builds_task_list_data(self):
        repo = FakeTaskRepository()
        use_case = GetTaskListUseCase(task_repo=repo)
        filters = TaskListFilters(topic_id='topic-1', search='сила')

        data = use_case.execute(filters, include_cache_stats=True)

        self.assertEqual(repo.filters, filters)
        self.assertEqual(data.tasks, ['task-1'])
        self.assertEqual(data.topics, ['topic-1'])
        self.assertEqual(data.analog_groups, ['group-1'])
        self.assertEqual(data.sources, ['source-1'])
        self.assertEqual(data.subtopics, ['subtopic-for-topic-1'])
        self.assertEqual(data.task_types, [('computational', 'Расчётная задача')])
        self.assertEqual(data.grade_choices[0], (7, '7 класс'))
        self.assertEqual(data.total_tasks, 7)
        self.assertEqual(data.ungrouped_count, 2)
        self.assertEqual(data.cache_stats, {'total': 7})
        self.assertTrue(repo.cache_stats_requested)

    def test_execute_skips_cache_stats_for_non_staff_context(self):
        repo = FakeTaskRepository()
        use_case = GetTaskListUseCase(task_repo=repo)

        data = use_case.execute(TaskListFilters())

        self.assertIsNone(data.cache_stats)
        self.assertFalse(repo.cache_stats_requested)
