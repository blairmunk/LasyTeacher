from unittest import TestCase

from core_logic.entities.task import TaskGroupListFilters
from core_logic.use_cases.get_task_group_list import GetTaskGroupListUseCase


class FakeTaskRepository:
    def __init__(self):
        self.filters = None

    def get_list_task_groups(self, filters):
        self.filters = filters
        return ['group-1']

    def get_list_topics(self):
        return ['topic-1']

    def get_subtopics_for_topic(self, topic_id):
        return [f'subtopic-for-{topic_id}'] if topic_id else []

    def count_analog_groups(self):
        return 5

    def count_empty_analog_groups(self):
        return 1

    def count_task_group_memberships(self):
        return 8


class GetTaskGroupListUseCaseTests(TestCase):
    def test_execute_builds_task_group_list_data(self):
        repo = FakeTaskRepository()
        use_case = GetTaskGroupListUseCase(task_repo=repo)
        filters = TaskGroupListFilters(topic_id='topic-1', search='скорость')

        data = use_case.execute(filters)

        self.assertEqual(repo.filters, filters)
        self.assertEqual(data.analog_groups, ['group-1'])
        self.assertEqual(data.topics, ['topic-1'])
        self.assertEqual(data.subtopics, ['subtopic-for-topic-1'])
        self.assertEqual(data.difficulties[0], (1, 'Базовый'))
        self.assertEqual(data.total_groups, 5)
        self.assertEqual(data.empty_groups, 1)
        self.assertEqual(data.total_tasks_in_groups, 8)
