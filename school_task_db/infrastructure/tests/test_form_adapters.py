from django.http import QueryDict
from django.test import SimpleTestCase

from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter


class TaskFormAdapterTests(SimpleTestCase):
    def test_builds_task_list_filters_from_query(self):
        query = QueryDict(
            'search=force&topic=t1&subtopic=s1&task_type=test'
            '&difficulty=2&group_filter=ungrouped&analog_group=g1'
            '&math_filter=with_math&source=src1&grade=9&verified=yes',
        )

        filters = TaskFormAdapter().task_list_filters_from_query(query)

        self.assertEqual(filters.search, 'force')
        self.assertEqual(filters.topic_id, 't1')
        self.assertEqual(filters.subtopic_id, 's1')
        self.assertEqual(filters.task_type, 'test')
        self.assertEqual(filters.difficulty, '2')
        self.assertEqual(filters.group_filter, 'ungrouped')
        self.assertEqual(filters.analog_group_id, 'g1')
        self.assertEqual(filters.math_filter, 'with_math')
        self.assertEqual(filters.source_id, 'src1')
        self.assertEqual(filters.grade, '9')
        self.assertEqual(filters.verified, 'yes')

    def test_builds_task_list_context_with_defaults(self):
        context = TaskFormAdapter().task_list_filter_context_from_query(QueryDict(''))

        self.assertEqual(context['current_source'], '')
        self.assertEqual(context['current_grade'], '')
        self.assertEqual(context['current_verified'], '')
        self.assertEqual(context['current_filter'], 'all')
        self.assertEqual(context['search_query'], '')
        self.assertEqual(context['current_topic'], '')
        self.assertEqual(context['current_subtopic'], '')
        self.assertEqual(context['current_task_type'], '')
        self.assertEqual(context['current_difficulty'], '')
        self.assertEqual(context['current_group_filter'], '')
        self.assertEqual(context['current_analog_group'], '')


class TaskGroupFormAdapterTests(SimpleTestCase):
    def test_builds_task_group_list_filters_from_query(self):
        query = QueryDict(
            'search=kinematics&topic=t1&subtopic=s1&difficulty=3'
            '&group_filter=empty&sort=-tasks&min_tasks=2&max_tasks=7',
        )

        filters = TaskGroupFormAdapter().task_group_list_filters_from_query(query)

        self.assertEqual(filters.search, 'kinematics')
        self.assertEqual(filters.topic_id, 't1')
        self.assertEqual(filters.subtopic_id, 's1')
        self.assertEqual(filters.difficulty, '3')
        self.assertEqual(filters.group_filter, 'empty')
        self.assertEqual(filters.sort, '-tasks')
        self.assertEqual(filters.min_tasks, '2')
        self.assertEqual(filters.max_tasks, '7')

    def test_builds_task_group_list_context_with_defaults(self):
        context = (
            TaskGroupFormAdapter()
            .task_group_list_filter_context_from_query(QueryDict(''))
        )

        self.assertEqual(context['search_query'], '')
        self.assertEqual(context['current_topic'], '')
        self.assertEqual(context['current_subtopic'], '')
        self.assertEqual(context['current_difficulty'], '')
        self.assertEqual(context['current_group_filter'], '')
        self.assertEqual(context['current_sort'], 'name')
        self.assertEqual(context['min_tasks'], '')
        self.assertEqual(context['max_tasks'], '')
