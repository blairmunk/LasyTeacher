from django.http import QueryDict
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.report_forms import ReportFormAdapter
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter


class CoreFormAdapterTests(SimpleTestCase):
    def test_builds_global_search_request_from_query(self):
        request = CoreFormAdapter().global_search_request_from_query(
            QueryDict('q=force'),
        )

        self.assertEqual(request.raw_query, 'force')

    def test_builds_task_import_file_request_from_upload(self):
        uploaded_file = SimpleUploadedFile(
            'tasks.json',
            b'{"tasks": []}',
            content_type='application/json',
        )

        request = CoreFormAdapter().task_import_file_request_from_upload(
            uploaded_file,
        )

        self.assertEqual(request.filename, 'tasks.json')
        self.assertEqual(request.file_size, len(b'{"tasks": []}'))
        self.assertEqual(request.content, b'{"tasks": []}')

    def test_builds_task_import_execution_submission_from_upload(self):
        uploaded_file = SimpleUploadedFile(
            'tasks.json',
            b'{"tasks": []}',
            content_type='application/json',
        )
        post_data = QueryDict('', mutable=True)
        post_data.update({'mode': 'append', 'dry_run': 'true'})
        post_data.setlist('create_missing', ['true'])

        request = CoreFormAdapter().task_import_execution_submission_from_upload(
            uploaded_file,
            post_data,
        )

        self.assertEqual(request.filename, 'tasks.json')
        self.assertEqual(request.file_size, len(b'{"tasks": []}'))
        self.assertEqual(request.content, b'{"tasks": []}')
        self.assertEqual(request.form_data['mode'], ['append'])
        self.assertEqual(request.form_data['dry_run'], ['true'])
        self.assertEqual(request.form_data['create_missing'], ['true'])

    def test_builds_task_import_validation_requests_from_data(self):
        data = {'tasks': []}
        adapter = CoreFormAdapter()

        validation_request = adapter.validate_task_import_json_request_from_data(data)
        preview_request = adapter.task_import_preview_request_from_data(data)

        self.assertIs(validation_request.data, data)
        self.assertIs(preview_request.data, data)

    def test_builds_export_tasks_request_from_query(self):
        request = CoreFormAdapter().export_tasks_request_from_query(
            QueryDict('topic=t1&subject=physics&grade=9'),
            export_date='2026-07-18',
        )

        self.assertEqual(request.filters.topic_id, 't1')
        self.assertEqual(request.filters.subject, 'physics')
        self.assertEqual(request.filters.grade, '9')
        self.assertEqual(request.export_date, '2026-07-18')


class ReportFormAdapterTests(SimpleTestCase):
    def test_builds_top_level_report_requests(self):
        adapter = ReportFormAdapter()
        now = object()

        dashboard = adapter.reports_dashboard_request(
            year=2026,
            current_date=now,
        )
        student_performance = adapter.student_performance_request_from_query(
            QueryDict('group=g1'),
            year=2026,
        )
        work_analysis = adapter.work_analysis_request(year=2026)
        events_status = adapter.events_status_request(
            year=2026,
            current_date=now,
        )

        self.assertEqual(dashboard.year, 2026)
        self.assertIs(dashboard.current_date, now)
        self.assertEqual(student_performance.year, 2026)
        self.assertEqual(student_performance.group_id, 'g1')
        self.assertEqual(work_analysis.year, 2026)
        self.assertEqual(events_status.year, 2026)
        self.assertIs(events_status.current_date, now)

    def test_builds_heatmap_params_and_requests_from_query(self):
        query = QueryDict('group=g1&section=Mechanics&transpose=1&subtopic=s1')
        adapter = ReportFormAdapter()

        params = adapter.heatmap_params_from_query(query)
        group_url_params = adapter.heatmap_group_url_params_from_query(query)
        overview = adapter.heatmap_overview_request_from_query(query)
        course = adapter.heatmap_course_overview_request_from_query(
            query,
            course_id='c1',
        )
        drilldown = adapter.heatmap_drilldown_overview_request_from_query(
            query,
            topic_id='t1',
        )
        student = adapter.heatmap_student_detail_request_from_query(
            query,
            topic_id='t1',
            student_id='st1',
        )
        subtopic = adapter.heatmap_subtopic_detail_request_from_query(
            query,
            subtopic_id='s1',
        )

        self.assertEqual(params, {
            'group_id': 'g1',
            'section': 'Mechanics',
            'transpose': True,
        })
        self.assertEqual(group_url_params, {
            'group_param': '?group=g1',
            'group_suffix': '&group=g1',
        })
        self.assertEqual(overview.group_id, 'g1')
        self.assertEqual(course.course_id, 'c1')
        self.assertEqual(course.group_id, 'g1')
        self.assertEqual(drilldown.topic_id, 't1')
        self.assertEqual(drilldown.group_id, 'g1')
        self.assertEqual(student.topic_id, 't1')
        self.assertEqual(student.student_id, 'st1')
        self.assertEqual(student.subtopic_id, 's1')
        self.assertEqual(subtopic.subtopic_id, 's1')
        self.assertEqual(subtopic.group_id, 'g1')

    def test_builds_journal_request_from_query(self):
        request = ReportFormAdapter().journal_request_from_query(
            QueryDict('debts=1'),
            course_id='c1',
            group_id='g1',
            year=2026,
        )

        self.assertEqual(request.course_id, 'c1')
        self.assertEqual(request.group_id, 'g1')
        self.assertEqual(request.year, 2026)
        self.assertTrue(request.show_debts_only)


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
    def test_builds_add_tasks_to_group_request_from_query(self):
        request = (
            TaskGroupFormAdapter()
            .add_tasks_to_group_form_request_from_query(
                QueryDict('search=force'),
                group_id='g1',
            )
        )

        self.assertEqual(request.group_id, 'g1')
        self.assertEqual(request.search, 'force')

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
