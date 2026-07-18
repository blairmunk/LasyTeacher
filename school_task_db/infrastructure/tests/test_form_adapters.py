from django.http import QueryDict
from django.test import SimpleTestCase

from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter


class CoreFormAdapterTests(SimpleTestCase):
    def test_builds_global_search_request_from_query(self):
        request = CoreFormAdapter().global_search_request_from_query(
            QueryDict('q=force'),
        )

        self.assertEqual(request.raw_query, 'force')


class TaskFormAdapterTests(SimpleTestCase):
    def test_builds_bulk_action_requests_from_body(self):
        adapter = TaskFormAdapter()
        body = {
            'task_ids': ['t1', 't2'],
            'group_name': 'New group',
            'group_id': 'g1',
            'work_name': 'Control work',
            'work_type': 'quiz',
        }

        create_group = adapter.bulk_create_group_request_from_body(body)
        add_to_group = adapter.bulk_add_to_group_request_from_body(body)
        remove = adapter.bulk_remove_from_groups_request_from_body(body)
        create_work = adapter.create_work_from_tasks_request_from_body(body)

        self.assertEqual(create_group.task_ids, ['t1', 't2'])
        self.assertEqual(create_group.group_name, 'New group')
        self.assertEqual(add_to_group.task_ids, ['t1', 't2'])
        self.assertEqual(add_to_group.group_id, 'g1')
        self.assertEqual(remove.task_ids, ['t1', 't2'])
        self.assertEqual(create_work.task_ids, ['t1', 't2'])
        self.assertEqual(create_work.work_name, 'Control work')
        self.assertEqual(create_work.work_type, 'quiz')

    def test_builds_reference_option_params_from_query(self):
        query = QueryDict('topic_id=t1&subject=physics&category=requirements')
        adapter = TaskFormAdapter()

        topic_id = adapter.subtopic_options_topic_id_from_query(query)
        codifier_params = adapter.codifier_elements_params_from_query(query)

        self.assertEqual(topic_id, 't1')
        self.assertEqual(codifier_params, {
            'subject': 'physics',
            'category': 'requirements',
        })

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
    def test_builds_group_bulk_action_requests_from_body(self):
        body = {
            'groups': [
                {'id': 'g1', 'order': '2', 'count': '3', 'weight': '4'},
                {'id': 'g2'},
            ],
            'work_name': 'From groups',
            'work_type': 'test',
            'max_score': '12',
            'auto_generate': True,
            'variant_count': '5',
            'group_ids': ['g1', 'g2'],
        }
        adapter = TaskGroupFormAdapter()

        create_work = adapter.create_work_from_groups_request_from_body(body)
        delete_groups = adapter.delete_task_groups_request_from_body(body)

        self.assertEqual(create_work.work_name, 'From groups')
        self.assertEqual(create_work.work_type, 'test')
        self.assertEqual(create_work.max_score, 12)
        self.assertTrue(create_work.auto_generate)
        self.assertEqual(create_work.variant_count, 5)
        self.assertEqual(create_work.groups[0].id, 'g1')
        self.assertEqual(create_work.groups[0].order, 2)
        self.assertEqual(create_work.groups[0].count, 3)
        self.assertEqual(create_work.groups[0].weight, 4)
        self.assertEqual(create_work.groups[1].id, 'g2')
        self.assertEqual(create_work.groups[1].order, 2)
        self.assertEqual(create_work.groups[1].count, 1)
        self.assertEqual(create_work.groups[1].weight, 1)
        self.assertEqual(delete_groups.group_ids, ['g1', 'g2'])

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
