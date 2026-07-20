from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.test import SimpleTestCase

from infrastructure.forms.document_template_django_forms import (
    DocumentTemplateForm,
)
from core_logic.entities.document import (
    DocumentPresentation,
    DocumentSectionSpec,
    DocumentTemplateSpec,
)
from core_logic.entities.document_rendering import (
    DocumentRenderResult,
    GeneratedDocumentFile,
)
from core_logic.entities.work import (
    WorkListData,
    WorkListFilters,
    WorkListItem,
)
from core_logic.use_cases.get_document_template_editor_data import (
    DocumentTemplateEditorData,
)
from core_logic.value_objects.document_render_options import WorkDocumentRenderOptions
from core_logic.value_objects.document_recipes import (
    HEADER_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.value_objects.document_section_catalog import (
    get_document_section_catalog,
)
from core_logic.value_objects.document_type_catalog import (
    get_document_type_catalog,
)
from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.document_template_forms import (
    DocumentTemplateFormAdapter,
)
from infrastructure.forms.report_forms import ReportFormAdapter
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter
from infrastructure.forms.work_forms import WorkFormAdapter


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


class DocumentTemplateFormAdapterTests(SimpleTestCase):
    def test_builds_editor_data_request_from_query(self):
        request = (
            DocumentTemplateFormAdapter()
            .editor_data_request_from_query(
                QueryDict('type=work&renderable=1&legacy=1'),
            )
        )

        self.assertEqual(request.document_type, WORK_DOCUMENT_TYPE)
        self.assertTrue(request.renderable_only)
        self.assertTrue(request.include_legacy_sections)

    def test_builds_editor_context(self):
        request = (
            DocumentTemplateFormAdapter()
            .editor_data_request_from_query(QueryDict('type=work'))
        )
        editor_data = DocumentTemplateEditorData(
            document_types=get_document_type_catalog(renderable_only=True),
            sections=get_document_section_catalog(document_type=WORK_DOCUMENT_TYPE),
            templates=[
                DocumentTemplateSpec(
                    name='Шаблон работы',
                    template_type=WORK_DOCUMENT_TYPE,
                    template_id='template-work',
                    sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
                    default_content_config={'answer_type': 'tasks_only'},
                    presentation=DocumentPresentation(custom_css='body {}'),
                )
            ],
        )

        context = DocumentTemplateFormAdapter().editor_context(
            editor_data,
            request,
        )

        self.assertEqual(context['current_document_type'], WORK_DOCUMENT_TYPE)
        self.assertFalse(context['renderable_only'])
        self.assertFalse(context['include_legacy_sections'])
        self.assertEqual(context['document_types'][0]['document_type'], 'work')
        self.assertEqual(
            context['document_types'][0]['renderer_labels'],
            ['HTML', 'PDF', 'LaTeX'],
        )
        self.assertEqual(context['document_types'][0]['url'], '?type=work')
        self.assertEqual(context['sections'][0]['section_type'], HEADER_SECTION)
        self.assertEqual(context['templates'][0]['template_id'], 'template-work')
        self.assertEqual(context['templates'][0]['name'], 'Шаблон работы')
        self.assertEqual(context['templates'][0]['sections_count'], 1)
        self.assertEqual(
            context['templates'][0]['default_content_config'],
            {'answer_type': 'tasks_only'},
        )
        self.assertTrue(context['templates'][0]['has_customization'])

    def test_editor_context_preserves_filter_flags_in_document_type_urls(self):
        request = (
            DocumentTemplateFormAdapter()
            .editor_data_request_from_query(
                QueryDict('type=work&renderable=1&legacy=1'),
            )
        )
        editor_data = DocumentTemplateEditorData(
            document_types=get_document_type_catalog(renderable_only=True),
            sections=(),
            templates=[],
        )

        context = DocumentTemplateFormAdapter().editor_context(
            editor_data,
            request,
        )

        self.assertEqual(
            context['document_types'][0]['url'],
            '?type=work&renderable=1&legacy=1',
        )

    def test_builds_create_params_from_template_form(self):
        form = DocumentTemplateForm(
            data=QueryDict(
                'name=Шаблон&description=Описание&template_type=work'
                '&sections=header&sections=task_list&is_default=on',
            ),
            sections=get_document_section_catalog(renderable_only=True),
        )
        self.assertTrue(form.is_valid(), form.errors)

        params = DocumentTemplateFormAdapter().create_params_from_form(form)

        self.assertEqual(params.name, 'Шаблон')
        self.assertEqual(params.description, 'Описание')
        self.assertEqual(params.template_type, 'work')
        self.assertEqual(params.section_types, ('header', 'task_list'))
        self.assertTrue(params.is_default)

    def test_builds_create_context(self):
        form = DocumentTemplateForm(
            data=QueryDict('template_type=work&sections=header'),
            sections=get_document_section_catalog(renderable_only=True),
        )

        context = DocumentTemplateFormAdapter().create_context(
            form=form,
            document_types=get_document_type_catalog(renderable_only=True),
            sections=get_document_section_catalog(renderable_only=True),
        )

        self.assertEqual(context['form'], form)
        self.assertEqual(context['selected_document_type'], 'work')
        self.assertEqual(context['selected_sections'], {'header'})
        self.assertEqual(context['section_options'][0]['section_type'], 'header')


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

    def test_builds_bulk_action_response_payloads(self):
        adapter = TaskFormAdapter()

        self.assertEqual(
            adapter.bulk_create_group_response_payload(
                SimpleNamespace(
                    group_id='g1',
                    group_name='Group',
                    added_count=2,
                    message='Created',
                )
            ),
            {
                'success': True,
                'group_id': 'g1',
                'group_name': 'Group',
                'added': 2,
                'message': 'Created',
            },
        )
        self.assertEqual(
            adapter.bulk_add_to_group_response_payload(
                SimpleNamespace(
                    added_count=1,
                    skipped_count=1,
                    message='Added',
                )
            ),
            {
                'success': True,
                'added': 1,
                'skipped': 1,
                'message': 'Added',
            },
        )
        self.assertEqual(
            adapter.bulk_remove_from_groups_response_payload(
                SimpleNamespace(removed_count=3, message='Removed')
            ),
            {
                'success': True,
                'removed': 3,
                'message': 'Removed',
            },
        )
        self.assertEqual(
            adapter.create_work_from_tasks_response_payload(
                SimpleNamespace(
                    work_id='w1',
                    variant_id='v1',
                    tasks_count=4,
                    message='Created work',
                )
            ),
            {
                'success': True,
                'work_id': 'w1',
                'variant_id': 'v1',
                'tasks_count': 4,
                'redirect_url': '/works/w1/',
                'message': 'Created work',
            },
        )


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

    def test_builds_group_bulk_action_response_payloads(self):
        adapter = TaskGroupFormAdapter()

        self.assertEqual(
            adapter.create_work_from_groups_response_payload(
                SimpleNamespace(
                    work_id='w1',
                    message='Created',
                    variants_generated=2,
                    warning='Partial',
                )
            ),
            {
                'success': True,
                'work_id': 'w1',
                'redirect_url': '/works/w1/',
                'message': 'Created',
                'variants_generated': 2,
                'warning': 'Partial',
            },
        )
        self.assertEqual(
            adapter.create_work_from_groups_response_payload(
                SimpleNamespace(
                    work_id='w1',
                    message='Created',
                    variants_generated=0,
                    warning='',
                )
            ),
            {
                'success': True,
                'work_id': 'w1',
                'redirect_url': '/works/w1/',
                'message': 'Created',
            },
        )
        self.assertEqual(
            adapter.delete_task_groups_response_payload(
                SimpleNamespace(deleted_count=2, message='Deleted')
            ),
            {
                'success': True,
                'deleted': 2,
                'message': 'Deleted',
            },
        )


class WorkFormAdapterTests(SimpleTestCase):
    def test_builds_work_list_filters_from_query(self):
        filters = WorkFormAdapter().work_list_filters_from_query(
            QueryDict(
                'q=контрольная&work_type=test'
                '&variant_status=with_variants&hide_remedial=1',
            ),
        )

        self.assertEqual(
            filters,
            WorkListFilters(
                q='контрольная',
                work_type='test',
                variant_status='with_variants',
                hide_remedial=True,
            ),
        )

    def test_builds_work_list_context(self):
        filters = WorkListFilters(work_type='remedial', hide_remedial=True)
        data = WorkListData(
            works=[
                WorkListItem(
                    pk='work-1',
                    name='Работа над ошибками',
                    duration=45,
                    created_at=None,
                    variant_count=2,
                    work_type='remedial',
                    work_type_display='Работа над ошибками',
                )
            ],
            filters=filters,
        )

        context = WorkFormAdapter().work_list_context(data)

        self.assertEqual(context['works'], data.works)
        self.assertEqual(context['filters'], filters)
        self.assertTrue(context['has_active_filters'])
        self.assertIn(
            {'value': 'remedial', 'label': 'Работа над ошибками'},
            context['work_type_options'],
        )
        self.assertIn(
            {'value': 'with_variants', 'label': 'С вариантами'},
            context['variant_status_options'],
        )

    def test_reads_document_renderer_type_from_post(self):
        adapter = WorkFormAdapter()

        self.assertEqual(
            adapter.document_renderer_type_from_post(QueryDict('renderer_type=html')),
            'html',
        )
        self.assertEqual(
            adapter.document_renderer_type_from_post(QueryDict('')),
            'pdf',
        )
        self.assertEqual(
            adapter.document_renderer_type_from_post(
                QueryDict(''),
                default='html',
            ),
            'html',
        )

    def test_builds_render_work_document_request_from_post(self):
        request = WorkFormAdapter().render_work_document_request_from_post(
            QueryDict(
                'renderer_type=html&format=A5&answer_type=with_short_solutions'
                '&include_hints=1&include_instructions=1'
                '&template_id=template-work',
            ),
            work_id='w1',
        )

        self.assertEqual(request.work_id, 'w1')
        self.assertEqual(request.template_id, 'template-work')
        self.assertEqual(request.options.renderer_type, 'html')
        self.assertEqual(request.options.pdf_format, 'A5')
        self.assertEqual(request.options.answer_type, 'with_short_solutions')
        self.assertTrue(request.options.include_hints)
        self.assertTrue(request.options.include_instructions)

    def test_builds_render_remedial_sheet_request_from_post(self):
        request = WorkFormAdapter().render_remedial_sheet_request_from_post(
            QueryDict(
                'renderer_type=pdf&format=A4'
                '&answer_type=with_full_solutions&template_id=template-rno',
            ),
            variant_id='v1',
        )

        self.assertEqual(request.variant_id, 'v1')
        self.assertEqual(request.template_id, 'template-rno')
        self.assertEqual(request.options.renderer_type, 'pdf')
        self.assertEqual(request.options.pdf_format, 'A4')
        self.assertEqual(request.options.answer_type, 'with_full_solutions')

    def test_builds_render_remedial_sheet_batch_request_from_post(self):
        request = WorkFormAdapter().render_remedial_sheet_batch_request_from_post(
            QueryDict('renderer_type=html&template_id=template-rno'),
            work_id='w1',
        )

        self.assertEqual(request.work_id, 'w1')
        self.assertEqual(request.template_id, 'template-rno')
        self.assertEqual(request.options.renderer_type, 'html')

    def test_builds_rendered_document_file_request(self):
        request = WorkFormAdapter().rendered_document_file_request(
            'html',
            'work.html',
        )

        self.assertEqual(request.file_type, 'html')
        self.assertEqual(request.filename, 'work.html')

    def test_builds_rendered_work_document_response_payload(self):
        payload = WorkFormAdapter().rendered_work_document_response_payload(
            DocumentRenderResult(
                status='generated',
                renderer_type='html',
                file_type='html',
                files=[GeneratedDocumentFile(filename='work.html', size_kb=1.25)],
            ),
            WorkDocumentRenderOptions(
                renderer_type='html',
                answer_type='with_answers',
            ),
        )

        self.assertEqual(payload, {
            'success': True,
            'message': 'HTML документ создан (с ответами)',
            'files': [
                {
                    'name': 'work.html',
                    'size': '1.2 KB',
                    'download_url': '/works/download/html/work.html/',
                },
            ],
            'total_files': 1,
        })

    def test_builds_remedial_sheet_response_payload(self):
        payload = WorkFormAdapter().remedial_sheet_response_payload(
            DocumentRenderResult(
                status='generated',
                renderer_type='pdf',
                file_type='pdf',
                files=[
                    GeneratedDocumentFile(
                        filename='remedial.pdf',
                        size_kb=2.0,
                    ),
                ],
            ),
        )

        self.assertEqual(payload, {
            'status': 'success',
            'files': [
                {
                    'filename': 'remedial.pdf',
                    'url': '/works/download/pdf/remedial.pdf/',
                },
            ],
            'message': 'Рабочий лист создан (PDF)',
        })
