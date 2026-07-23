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
from core_logic.entities.core import (
    DashboardSummaryData,
    GlobalSearchData,
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
from core_logic.entities.report import ReportsDashboardData
from core_logic.entities.student import StudentRemedialWorkData
from core_logic.services.analytics_service import (
    ScoreTimelinePoint,
    StudentProfileData,
)
from core_logic.use_cases.get_document_template_editor_data import (
    DocumentTemplateEditorData,
)
from core_logic.value_objects.document_render_options import (
    WORK_DOCUMENT_STYLE_WORKSHEET,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_recipes import (
    COMMON_HEADER_SECTION,
    HEADER_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_DEMO,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
from core_logic.value_objects.document_section_catalog import (
    get_document_section_catalog,
)
from core_logic.value_objects.document_type_catalog import (
    get_document_type_catalog,
)
from infrastructure.forms.codifier_forms import CodifierFormAdapter
from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.curriculum_forms import CurriculumFormAdapter
from infrastructure.forms.document_template_forms import (
    DocumentTemplateFormAdapter,
)
from infrastructure.forms.event_forms import EventFormAdapter
from infrastructure.forms.report_forms import ReportFormAdapter
from infrastructure.forms.review_forms import ReviewFormAdapter
from infrastructure.forms.settings_forms import SettingsFormAdapter
from infrastructure.forms.student_forms import StudentFormAdapter
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter
from infrastructure.forms.work_forms import WorkFormAdapter


class CoreFormAdapterTests(SimpleTestCase):
    def test_builds_dashboard_summary_context(self):
        summary = DashboardSummaryData(
            tasks_count=1,
            works_count=2,
            variants_count=3,
            orphan_variants_count=4,
            students_count=5,
            events_count=6,
            groups_count=7,
        )

        context = CoreFormAdapter().dashboard_summary_context(summary)

        self.assertEqual(context['tasks_count'], 1)
        self.assertEqual(context['works_count'], 2)
        self.assertEqual(context['variants_count'], 3)
        self.assertEqual(context['orphan_variants_count'], 4)
        self.assertEqual(context['students_count'], 5)
        self.assertEqual(context['events_count'], 6)
        self.assertEqual(context['groups_count'], 7)

    def test_builds_global_search_request_from_query(self):
        request = CoreFormAdapter().global_search_request_from_query(
            QueryDict('q=force'),
        )

        self.assertEqual(request.raw_query, 'force')

    def test_builds_global_search_context(self):
        search_data = GlobalSearchData(
            query='force',
            results={'tasks': ['task-1']},
            total_found=1,
            search_mode='text',
            found_text='1 результат',
        )

        context = CoreFormAdapter().global_search_context(search_data)

        self.assertEqual(context['query'], 'force')
        self.assertEqual(context['results'], {'tasks': ['task-1']})
        self.assertEqual(context['total_found'], 1)
        self.assertEqual(context['search_mode'], 'text')
        self.assertEqual(context['found_text'], '1 результат')

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

    def test_builds_export_tasks_request_from_query(self):
        request = CoreFormAdapter().export_tasks_request_from_query(
            QueryDict('topic=t1&subject=physics&grade=9'),
            export_date='2026-07-18',
        )

        self.assertEqual(request.filters.topic_id, 't1')
        self.assertEqual(request.filters.subject, 'physics')
        self.assertEqual(request.filters.grade, '9')
        self.assertEqual(request.export_date, '2026-07-18')


class CodifierFormAdapterTests(SimpleTestCase):
    def test_builds_codifier_list_context(self):
        list_data = SimpleNamespace(codifiers=['codifier-1'])

        context = CodifierFormAdapter().codifier_list_context(list_data)

        self.assertEqual(context, {'codifiers': ['codifier-1']})

    def test_builds_codifier_detail_context(self):
        detail = SimpleNamespace(
            codifier='codifier-1',
            content_tree=['entry-1'],
            requirements=['requirement-1'],
            coverage={'total': 2, 'covered': 1},
        )

        context = CodifierFormAdapter().codifier_detail_context(detail)

        self.assertEqual(
            context,
            {
                'codifier': 'codifier-1',
                'content_tree': ['entry-1'],
                'requirements': ['requirement-1'],
                'coverage': {'total': 2, 'covered': 1},
            },
        )


class CurriculumFormAdapterTests(SimpleTestCase):
    def test_builds_topic_list_context_with_pagination(self):
        list_data = SimpleNamespace(topics=['topic-1', 'topic-2', 'topic-3'])

        context = CurriculumFormAdapter().topic_list_context(
            list_data,
            page_number='1',
            paginate_by=2,
        )

        self.assertEqual(list(context['topics']), ['topic-1', 'topic-2'])
        self.assertTrue(context['is_paginated'])
        self.assertEqual(context['page_obj'].number, 1)

    def test_builds_curriculum_detail_contexts_and_payload(self):
        adapter = CurriculumFormAdapter()
        topic_detail = SimpleNamespace(topic='topic-1', subtopics=['subtopic-1'])
        course_list = SimpleNamespace(courses=['course-1'])
        course_detail = SimpleNamespace(
            course='course-1',
            assignments=['assignment-1'],
            total_variants=3,
            works_by_type={'КР': 1},
            groups_coverage={'Алгебра': 2},
        )
        subtopics_data = SimpleNamespace(subtopics=[{'id': 'subtopic-1'}])

        self.assertEqual(
            adapter.topic_detail_context(topic_detail),
            {'topic': 'topic-1', 'subtopics': ['subtopic-1']},
        )
        self.assertEqual(
            adapter.course_list_context(course_list),
            {'courses': ['course-1']},
        )
        self.assertEqual(
            adapter.course_detail_context(course_detail),
            {
                'course': 'course-1',
                'assignments': ['assignment-1'],
                'total_variants': 3,
                'works_by_type': {'КР': 1},
                'groups_coverage': {'Алгебра': 2},
            },
        )
        self.assertEqual(
            adapter.topic_subtopics_payload(subtopics_data),
            {'subtopics': [{'id': 'subtopic-1'}]},
        )


class DocumentTemplateFormAdapterTests(SimpleTestCase):
    def _template_form(self, *args, sections=None, **kwargs):
        return DocumentTemplateForm(
            *args,
            document_types=get_document_type_catalog(renderable_only=True),
            sections=(
                sections
                if sections is not None
                else get_document_section_catalog(renderable_only=True)
            ),
            **kwargs,
        )

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
            print_profiles=[
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
        self.assertEqual(
            context['sections'][0]['section_type'],
            COMMON_HEADER_SECTION,
        )
        self.assertTrue(context['sections'][0]['is_fixed_order'])
        self.assertEqual(context['sections'][1]['section_type'], HEADER_SECTION)
        self.assertEqual(
            context['print_profiles'][0]['template_id'],
            'template-work',
        )
        self.assertEqual(context['print_profiles'][0]['name'], 'Шаблон работы')
        self.assertEqual(context['print_profiles'][0]['sections_count'], 1)
        self.assertEqual(
            context['print_profiles'][0]['default_content_config'],
            {'answer_type': 'tasks_only'},
        )
        self.assertTrue(context['print_profiles'][0]['has_customization'])
        self.assertEqual(context['templates'][0]['template_id'], 'template-work')

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
            print_profiles=[],
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
        form = self._template_form(
            data=QueryDict(
                'name=Шаблон&description=Описание&template_type=work'
                '&sections=header&sections=task_list&is_default=on',
            ),
        )
        self.assertTrue(form.is_valid(), form.errors)

        params = DocumentTemplateFormAdapter().create_params_from_form(form)

        self.assertEqual(params.name, 'Шаблон')
        self.assertEqual(params.description, 'Описание')
        self.assertEqual(params.template_type, 'work')
        self.assertEqual(params.section_types, ('header', 'task_list'))
        self.assertEqual(
            [section.section_type for section in params.sections],
            ['header', 'task_list'],
        )
        self.assertTrue(params.is_default)

    def test_builds_create_params_preserving_section_order(self):
        form = self._template_form(
            data=QueryDict(
                'name=Шаблон&template_type=work'
                '&sections=header&sections=task_list'
                '&section_order=task_list,header',
            ),
        )
        self.assertTrue(form.is_valid(), form.errors)

        params = DocumentTemplateFormAdapter().create_params_from_form(form)

        self.assertEqual(params.section_types, ('task_list', 'header'))
        self.assertEqual(
            [section.section_type for section in params.sections],
            ['task_list', 'header'],
        )

    def test_builds_create_params_with_common_header_fixed_first(self):
        form = self._template_form(
            data=QueryDict(
                'name=Шаблон&template_type=work'
                '&sections=header&sections=common_header&sections=task_list'
                '&section_order=task_list,header,common_header',
            ),
        )
        self.assertTrue(form.is_valid(), form.errors)

        params = DocumentTemplateFormAdapter().create_params_from_form(form)

        self.assertEqual(
            params.section_types,
            ('common_header', 'task_list', 'header'),
        )

    def test_builds_create_params_with_repeated_sections_from_order(self):
        form = self._template_form(
            data=QueryDict(
                'name=Шаблон&template_type=work'
                '&sections=header&sections=task_list&sections=page_break'
                '&section_order=header,task_list,page_break,header,task_list',
            ),
        )
        self.assertTrue(form.is_valid(), form.errors)

        params = DocumentTemplateFormAdapter().create_params_from_form(form)

        self.assertEqual(
            params.section_types,
            ('header', 'task_list', 'page_break', 'header', 'task_list'),
        )

    def test_builds_create_params_with_section_options(self):
        data = QueryDict('', mutable=True)
        data.update({'name': 'Шаблон', 'template_type': 'work'})
        data.setlist('sections', ['header', 'task_list'])
        data['section_options__task_list'] = (
            '{"hidden_roles": ["demo"], "role_blank_cells": {"practice": 6}}'
        )
        form = self._template_form(
            data=data,
        )
        self.assertTrue(form.is_valid(), form.errors)

        params = DocumentTemplateFormAdapter().create_params_from_form(form)

        self.assertEqual(params.section_types, ('header', 'task_list'))
        self.assertEqual(params.sections[0].options, {})
        self.assertEqual(
            params.sections[1].options,
            {
                'hidden_roles': ['demo'],
                'role_blank_cells': {'practice': 6},
            },
        )

    def test_template_form_rejects_invalid_section_options_json(self):
        data = QueryDict('', mutable=True)
        data.update({'name': 'Шаблон', 'template_type': 'work'})
        data.setlist('sections', ['task_list'])
        data['section_options__task_list'] = '{"hidden_roles":'
        form = self._template_form(
            data=data,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Настройки секции task_list: некорректный JSON.',
            form.non_field_errors(),
        )

    def test_template_form_rejects_non_object_section_options_json(self):
        data = QueryDict('', mutable=True)
        data.update({'name': 'Шаблон', 'template_type': 'work'})
        data.setlist('sections', ['task_list'])
        data['section_options__task_list'] = '["demo"]'
        form = self._template_form(
            data=data,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Настройки секции task_list должны быть JSON-объектом.',
            form.non_field_errors(),
        )

    def test_builds_update_params_from_template_form(self):
        form = self._template_form(
            data=QueryDict(
                'name=Шаблон&description=Описание&template_type=work'
                '&sections=header',
            ),
        )
        self.assertTrue(form.is_valid(), form.errors)

        params = DocumentTemplateFormAdapter().update_params_from_form(
            form,
            template_id='template-1',
        )

        self.assertEqual(params.template_id, 'template-1')
        self.assertEqual(params.name, 'Шаблон')
        self.assertEqual(params.section_types, ('header',))
        self.assertEqual(
            [section.section_type for section in params.sections],
            ['header'],
        )
        self.assertFalse(params.is_default)

    def test_builds_form_initial_from_template(self):
        template = DocumentTemplateSpec(
            name='Шаблон',
            template_type=WORK_DOCUMENT_TYPE,
            template_id='template-1',
            description='Описание',
            is_default=True,
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )

        initial = DocumentTemplateFormAdapter().form_initial_from_template(
            template,
        )

        self.assertEqual(initial['name'], 'Шаблон')
        self.assertEqual(initial['description'], 'Описание')
        self.assertEqual(initial['template_type'], WORK_DOCUMENT_TYPE)
        self.assertEqual(initial['sections'], (HEADER_SECTION,))
        self.assertEqual(initial['section_order'], HEADER_SECTION)
        self.assertTrue(initial['is_default'])

    def test_builds_form_initial_with_section_options_from_template(self):
        template = DocumentTemplateSpec(
            name='Шаблон',
            template_type=WORK_DOCUMENT_TYPE,
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(
                    section_type='task_list',
                    options={
                        'hidden_roles': ['demo'],
                        'role_blank_cells': {'practice': {'rows': 6}},
                    },
                ),
            ],
        )

        initial = DocumentTemplateFormAdapter().form_initial_from_template(
            template,
        )

        self.assertEqual(
            initial['section_options'],
            {
                'task_list': {
                    'hidden_roles': ['demo'],
                    'role_blank_cells': {'practice': {'rows': 6}},
                },
            },
        )

    def test_builds_create_context(self):
        form = self._template_form(
            data=QueryDict('template_type=work&sections=header'),
        )

        context = DocumentTemplateFormAdapter().create_context(
            form=form,
            document_types=get_document_type_catalog(renderable_only=True),
            sections=get_document_section_catalog(renderable_only=True),
        )

        self.assertEqual(context['form'], form)
        self.assertEqual(context['selected_document_type'], 'work')
        self.assertEqual(context['selected_sections'], {'header'})
        self.assertEqual(context['selected_section_order'], ['header'])
        self.assertEqual(
            context['section_options'][0]['section_type'],
            COMMON_HEADER_SECTION,
        )
        self.assertTrue(context['section_options'][0]['is_fixed_order'])
        self.assertFalse(context['section_options'][0]['is_repeatable'])
        self.assertFalse(context['section_options'][0]['has_options'])
        self.assertIn('task_list', context['repeatable_section_types'])
        self.assertIn('page_break', context['repeatable_section_types'])

        task_list_context = next(
            section
            for section in context['section_options']
            if section['section_type'] == 'task_list'
        )
        self.assertTrue(task_list_context['has_options'])
        self.assertTrue(task_list_context['is_repeatable'])
        self.assertIn(
            'role_render_modes',
            task_list_context['options_example_json'],
        )
        self.assertIn('Можно скрывать роли', task_list_context['options_hint'])

    def test_builds_create_context_with_section_options_json(self):
        form = self._template_form(
            initial={
                'template_type': WORK_DOCUMENT_TYPE,
                'sections': ['task_list'],
                'section_options': {
                    'task_list': {
                        'hidden_roles': ['demo'],
                        'role_blank_cells': {'practice': 6},
                    },
                },
            },
        )

        context = DocumentTemplateFormAdapter().create_context(
            form=form,
            document_types=get_document_type_catalog(renderable_only=True),
            sections=get_document_section_catalog(renderable_only=True),
        )
        task_list_context = next(
            section
            for section in context['section_options']
            if section['section_type'] == 'task_list'
        )

        self.assertEqual(
            task_list_context['options_field_name'],
            'section_options__task_list',
        )
        self.assertIn('"hidden_roles": [', task_list_context['options_json'])
        self.assertIn('"role_blank_cells": {', task_list_context['options_json'])


class EventFormAdapterTests(SimpleTestCase):
    def test_builds_event_list_and_detail_contexts(self):
        event_list = SimpleNamespace(
            events=['event-1'],
            planned_events=['planned-1'],
            active_events=['active-1'],
            graded_events=['graded-1'],
        )
        detail = SimpleNamespace(
            event='event-1',
            participations=['participation-1'],
            some_variants_assigned=True,
            all_variants_assigned=False,
            can_review=True,
            status_color='warning',
            status_steps=['step-1'],
            available_variants=['variant-1'],
            status_transitions=['transition-1'],
        )

        adapter = EventFormAdapter()
        list_context = adapter.event_list_context(event_list)
        detail_context = adapter.event_detail_context(detail)

        self.assertEqual(list_context['events'], ['event-1'])
        self.assertEqual(list_context['planned_events'], ['planned-1'])
        self.assertEqual(list_context['active_events'], ['active-1'])
        self.assertEqual(list_context['graded_events'], ['graded-1'])
        self.assertEqual(detail_context['event'], 'event-1')
        self.assertEqual(detail_context['participations'], ['participation-1'])
        self.assertTrue(detail_context['some_variants_assigned'])
        self.assertFalse(detail_context['all_variants_assigned'])
        self.assertTrue(detail_context['can_review'])
        self.assertEqual(detail_context['status_color'], 'warning')
        self.assertEqual(detail_context['status_steps'], ['step-1'])
        self.assertEqual(detail_context['available_variants'], ['variant-1'])
        self.assertEqual(detail_context['status_transitions'], ['transition-1'])

    def test_builds_event_form_contexts(self):
        adapter = EventFormAdapter()
        form = object()
        event = object()

        create_context = adapter.event_create_context(form)
        update_context = adapter.event_update_context(event, form)

        self.assertEqual(create_context['form'], form)
        self.assertEqual(create_context['page_title'], 'Создание события')
        self.assertEqual(create_context['submit_text'], 'Создать')
        self.assertEqual(update_context['object'], event)
        self.assertEqual(update_context['form'], form)
        self.assertEqual(update_context['page_title'], 'Редактирование события')
        self.assertEqual(update_context['submit_text'], 'Сохранить')

    def test_builds_event_action_form_contexts(self):
        adapter = EventFormAdapter()
        form = object()
        selection_data = SimpleNamespace(
            event='event-1',
            current_participants=['student-1'],
        )
        assignment_data = SimpleNamespace(event='event-1')

        selection_context = adapter.participant_selection_context(
            selection_data,
            form,
        )
        assignment_context = adapter.variant_assignment_context(
            assignment_data,
            form,
        )

        self.assertEqual(selection_context['event'], 'event-1')
        self.assertEqual(selection_context['form'], form)
        self.assertEqual(
            selection_context['current_participants'],
            ['student-1'],
        )
        self.assertEqual(assignment_context['event'], 'event-1')
        self.assertEqual(assignment_context['form'], form)


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

    def test_builds_reports_dashboard_context(self):
        report = ReportsDashboardData(
            total_students=3,
            total_events=4,
            total_works=5,
            total_courses=2,
            total_marks=6,
            average_score=4.2,
            marks_last_month=1,
            score_counts={2: 0, 3: 1, 4: 2, 5: 3},
            events_planned=1,
            events_completed=2,
            events_graded=1,
            monthly_labels=['Июль'],
            monthly_values=[3],
            class_stats=[{'name': '7А'}],
            class_names=['7А'],
            class_avg_scores=[4.2],
            class_completion=[50],
            recent_events=['event-1'],
            event_status_counts={'planned': 1, 'graded': 2},
            box_data={'КР': [4, 5]},
            courses=['course-1'],
        )

        context = ReportFormAdapter().reports_dashboard_context(report)

        self.assertEqual(context['total_students'], 3)
        self.assertEqual(context['class_stats'], [{'name': '7А'}])
        self.assertEqual(context['recent_events'], ['event-1'])
        self.assertIn('score_chart_json', context)
        self.assertIn('activity_chart_json', context)
        self.assertIn('class_chart_json', context)
        self.assertIn('gauge_json', context)
        self.assertIn('donut_json', context)
        self.assertIn('box_plot_json', context)
        self.assertIn('Запланировано', context['donut_json'])
        self.assertIn('Проверено', context['donut_json'])

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


class ReviewFormAdapterTests(SimpleTestCase):
    def test_builds_review_dashboard_context(self):
        dashboard = SimpleNamespace(
            needs_review=['event-1'],
            in_progress=['event-2'],
            fully_graded=['event-3'],
            total_events=3,
        )

        context = ReviewFormAdapter().dashboard_context(
            dashboard,
            recent_sessions=['session-1'],
        )

        self.assertEqual(context['needs_review'], ['event-1'])
        self.assertEqual(context['in_progress'], ['event-2'])
        self.assertEqual(context['fully_graded'], ['event-3'])
        self.assertEqual(context['total_events'], 3)
        self.assertEqual(context['recent_sessions'], ['session-1'])

    def test_builds_event_review_context(self):
        review_data = SimpleNamespace(
            event='event-1',
            has_participants=True,
            variants_assigned=True,
            all_variants_assigned=False,
            blocked=False,
            block_reason='',
            available_variants=['variant-1'],
            participations_data=['participation-1'],
            total_participants=2,
            active_participants=2,
            graded_participants=1,
            absent_participants=0,
            progress_percentage=50,
            avg_score=4.0,
            score_distribution={4: 1},
        )

        context = ReviewFormAdapter().event_review_context(
            review_data,
            review_session='session-1',
        )

        self.assertEqual(context['event'], 'event-1')
        self.assertTrue(context['has_participants'])
        self.assertTrue(context['variants_assigned'])
        self.assertFalse(context['all_variants_assigned'])
        self.assertFalse(context['blocked'])
        self.assertEqual(context['available_variants'], ['variant-1'])
        self.assertEqual(context['participations_data'], ['participation-1'])
        self.assertEqual(context['total_participants'], 2)
        self.assertEqual(context['active_participants'], 2)
        self.assertEqual(context['graded_participants'], 1)
        self.assertEqual(context['progress_percentage'], 50)
        self.assertEqual(context['review_session'], 'session-1')

    def test_builds_participation_review_context_and_score_payload(self):
        review_data = SimpleNamespace(
            participation='participation-1',
            mark='mark-1',
            tasks_with_scores=['task-1'],
            typical_comments=['comment-1'],
            previous_participation='previous-1',
            next_participation='next-1',
            current_position=2,
            total_positions=5,
            navigation_progress=40,
        )
        result = SimpleNamespace(score=4, percentage=75.0)
        adapter = ReviewFormAdapter()

        context = adapter.participation_review_context(review_data)
        payload = adapter.score_calculation_payload(result)

        self.assertEqual(context['participation'], 'participation-1')
        self.assertEqual(context['mark'], 'mark-1')
        self.assertEqual(context['tasks_with_scores'], ['task-1'])
        self.assertEqual(context['typical_comments'], ['comment-1'])
        self.assertEqual(context['previous_participation'], 'previous-1')
        self.assertEqual(context['next_participation'], 'next-1')
        self.assertEqual(context['current_position'], 2)
        self.assertEqual(context['total_positions'], 5)
        self.assertEqual(context['navigation_progress'], 40)
        self.assertEqual(payload, {'score': 4, 'percentage': 75.0})


class SettingsFormAdapterTests(SimpleTestCase):
    def test_builds_settings_context(self):
        settings = object()
        form = object()

        context = SettingsFormAdapter().settings_context(settings, form)

        self.assertEqual(context, {'object': settings, 'form': form})


class StudentFormAdapterTests(SimpleTestCase):
    def test_builds_student_detail_context_with_charts(self):
        student = SimpleNamespace(pk='student-1', short_name='И. Иванов')
        profile = StudentProfileData(
            student_groups=['7А'],
            participations_data=['participation-1'],
            stats={
                'graded_works': 2,
                'score_counts': {2: 0, 3: 0, 4: 1, 5: 1},
                'avg_score': 4.5,
            },
            group_scores=[{'name': 'Алгебра', 'avg': 4.5}],
            scores_timeline=[
                ScoreTimelinePoint(date='01.09.2026', score=4, work='КР 1'),
                ScoreTimelinePoint(date='02.09.2026', score=5, work='КР 2'),
            ],
            task_log_stats={'total': 1},
            heatmap_groups=[{'name': 'Алгебра'}],
            heatmap_topics=[{'name': 'Линейные уравнения'}],
            heatmap_difficulty=[{'name': '2'}],
            recent_task_log=['log-1'],
        )

        context = StudentFormAdapter().student_detail_context(student, profile)

        self.assertEqual(context['student'], student)
        self.assertEqual(context['object'], student)
        self.assertEqual(context['student_groups'], ['7А'])
        self.assertEqual(context['participations_data'], ['participation-1'])
        self.assertEqual(context['recent_task_log'], ['log-1'])
        self.assertIn('mini_heatmap_json', context)
        self.assertIn('dynamics_chart_json', context)
        self.assertIn('score_chart_json', context)
        self.assertIn('Успеваемость по темам', context['mini_heatmap_json'])
        self.assertIn('Динамика оценок', context['dynamics_chart_json'])
        self.assertIn('Распределение оценок', context['score_chart_json'])

    def test_student_detail_context_omits_empty_charts(self):
        student = SimpleNamespace(pk='student-1', short_name='И. Иванов')
        profile = StudentProfileData(stats={})

        context = StudentFormAdapter().student_detail_context(student, profile)

        self.assertNotIn('mini_heatmap_json', context)
        self.assertNotIn('dynamics_chart_json', context)
        self.assertNotIn('score_chart_json', context)

    def test_builds_student_remedial_context(self):
        student = SimpleNamespace(pk='student-1')
        remedial_data = StudentRemedialWorkData(
            remedial_groups=['group-1'],
            weak_topics=['topic-1'],
            total_available=3,
            done_count=1,
        )

        context = StudentFormAdapter().student_remedial_context(
            student,
            remedial_data,
        )

        self.assertEqual(context['student'], student)
        self.assertEqual(context['object'], student)
        self.assertEqual(context['remedial_groups'], ['group-1'])
        self.assertEqual(context['weak_topics'], ['topic-1'])
        self.assertEqual(context['total_available'], 3)
        self.assertEqual(context['done_count'], 1)
        self.assertNotIn('no_data', context)

    def test_student_remedial_context_handles_no_data(self):
        student = SimpleNamespace(pk='student-1')
        remedial_data = StudentRemedialWorkData(no_data=True)

        context = StudentFormAdapter().student_remedial_context(
            student,
            remedial_data,
        )

        self.assertEqual(context['student'], student)
        self.assertTrue(context['no_data'])
        self.assertNotIn('remedial_groups', context)

    def test_builds_remedial_wizard_contexts(self):
        start_data = SimpleNamespace(
            groups=['7А'],
            limit_choices=(('tasks', 'По количеству заданий'),),
        )
        preview_data = SimpleNamespace(
            group='7А',
            preview=['row-1'],
            threshold=70,
            limit_type='tasks',
            limit_value=10,
            work_name='Работа над ошибками',
            students_with_tasks=2,
            total_tasks=5,
        )

        adapter = StudentFormAdapter()
        start_context = adapter.remedial_wizard_start_context(start_data)
        preview_context = adapter.remedial_wizard_preview_context(preview_data)

        self.assertEqual(start_context['groups'], ['7А'])
        self.assertEqual(
            start_context['limit_choices'],
            (('tasks', 'По количеству заданий'),),
        )
        self.assertEqual(preview_context['group'], '7А')
        self.assertEqual(preview_context['preview'], ['row-1'])
        self.assertEqual(preview_context['threshold'], 70)
        self.assertEqual(preview_context['students_with_tasks'], 2)
        self.assertEqual(preview_context['total_tasks'], 5)

    def test_builds_remedial_event_and_solutions_contexts(self):
        event_result = SimpleNamespace(
            event='event-1',
            work='work-1',
            analysis=['row-1'],
            weak_students=1,
        )
        sheet_data = SimpleNamespace(
            variant='variant-1',
            student='student-1',
            source_work='source-work-1',
            original_tasks=['original-task-1'],
            new_tasks=['new-task-1'],
            mark='mark-1',
        )

        adapter = StudentFormAdapter()
        event_context = adapter.remedial_event_preview_context(event_result)
        solutions_context = adapter.remedial_solutions_context(sheet_data)

        self.assertEqual(event_context['event'], 'event-1')
        self.assertEqual(event_context['work'], 'work-1')
        self.assertEqual(event_context['analysis'], ['row-1'])
        self.assertEqual(event_context['weak_students'], 1)
        self.assertEqual(solutions_context['variant'], 'variant-1')
        self.assertEqual(solutions_context['student'], 'student-1')
        self.assertEqual(solutions_context['source_work'], 'source-work-1')
        self.assertEqual(solutions_context['original_tasks'], ['original-task-1'])
        self.assertEqual(solutions_context['new_tasks'], ['new-task-1'])
        self.assertEqual(solutions_context['mark'], 'mark-1')


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

    def test_builds_task_list_context_with_pagination_and_stats(self):
        list_data = SimpleNamespace(
            tasks=['task-1', 'task-2', 'task-3'],
            topics=['topic-1'],
            analog_groups=['group-1'],
            sources=['source-1'],
            grade_choices=[(9, '9 класс')],
            subtopics=['subtopic-1'],
            task_types=[('test', 'Тест')],
            difficulties=[(1, 'Легкая')],
            total_tasks=3,
            ungrouped_count=1,
            cache_stats={'with_math': 2},
        )

        context = TaskFormAdapter().task_list_context(
            list_data,
            QueryDict('page=1&search=force'),
            paginate_by=2,
        )

        self.assertEqual(list(context['tasks']), ['task-1', 'task-2'])
        self.assertTrue(context['is_paginated'])
        self.assertEqual(context['topics'], ['topic-1'])
        self.assertEqual(context['analog_groups'], ['group-1'])
        self.assertEqual(context['sources'], ['source-1'])
        self.assertEqual(context['grade_choices'], [(9, '9 класс')])
        self.assertEqual(context['subtopics'], ['subtopic-1'])
        self.assertEqual(context['task_types'], [('test', 'Тест')])
        self.assertEqual(context['difficulties'], [(1, 'Легкая')])
        self.assertEqual(context['total_tasks'], 3)
        self.assertEqual(context['ungrouped_count'], 1)
        self.assertEqual(context['cache_stats'], {'with_math': 2})
        self.assertEqual(context['search_query'], 'force')

    def test_builds_task_page_contexts(self):
        adapter = TaskFormAdapter()
        form = object()
        image_formset = object()
        task = object()
        detail_data = SimpleNamespace(
            task='task-1',
            task_groups=['group-1'],
        )

        self.assertEqual(
            adapter.task_detail_context(detail_data),
            {'task': 'task-1', 'task_groups': ['group-1']},
        )
        self.assertEqual(
            adapter.task_create_context(form, image_formset),
            {'form': form, 'image_formset': image_formset},
        )
        self.assertEqual(
            adapter.task_update_context(task, form, image_formset),
            {'object': task, 'form': form, 'image_formset': image_formset},
        )
        self.assertEqual(
            adapter.task_delete_context(detail_data, '/tasks/1/'),
            {'task': 'task-1', 'cancel_url': '/tasks/1/'},
        )

    def test_builds_source_contexts(self):
        adapter = TaskFormAdapter()
        source_list = SimpleNamespace(sources=['source-1'])
        form = object()

        self.assertEqual(
            adapter.source_list_context(source_list),
            {'sources': ['source-1']},
        )
        self.assertEqual(adapter.source_create_context(form), {'form': form})

    def test_builds_reference_option_payloads(self):
        adapter = TaskFormAdapter()
        subtopics = SimpleNamespace(
            subtopics=[
                SimpleNamespace(id='s1', name='Кинематика'),
            ],
        )
        elements = SimpleNamespace(
            elements=[
                SimpleNamespace(code='1.1', name='Механика'),
            ],
        )

        self.assertEqual(
            adapter.subtopic_options_payload(subtopics),
            {'subtopics': [{'id': 's1', 'name': 'Кинематика'}]},
        )
        self.assertEqual(
            adapter.codifier_elements_payload(elements),
            {'elements': [{'code': '1.1', 'name': 'Механика'}]},
        )

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

    def test_builds_group_bulk_delete_request_from_body(self):
        body = {
            'group_ids': ['g1', 'g2'],
        }
        adapter = TaskGroupFormAdapter()

        delete_groups = adapter.delete_task_groups_request_from_body(body)

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

    def test_builds_task_group_list_context_with_pagination_and_stats(self):
        list_data = SimpleNamespace(
            analog_groups=['group-1', 'group-2', 'group-3'],
            topics=['topic-1'],
            subtopics=['subtopic-1'],
            difficulties=[(1, 'Легкая')],
            total_groups=3,
            empty_groups=1,
            total_tasks_in_groups=7,
        )

        context = TaskGroupFormAdapter().task_group_list_context(
            list_data,
            QueryDict('page=1&search=force'),
            paginate_by=2,
        )

        self.assertEqual(list(context['analog_groups']), ['group-1', 'group-2'])
        self.assertTrue(context['is_paginated'])
        self.assertEqual(context['topics'], ['topic-1'])
        self.assertEqual(context['subtopics'], ['subtopic-1'])
        self.assertEqual(context['difficulties'], [(1, 'Легкая')])
        self.assertEqual(context['total_groups'], 3)
        self.assertEqual(context['empty_groups'], 1)
        self.assertEqual(context['total_tasks_in_groups'], 7)
        self.assertEqual(context['search_query'], 'force')
        self.assertEqual(
            context['bank_role_filter_options'][0],
            (TASK_BANK_ROLE_ANY, 'Любая роль'),
        )

    def test_builds_task_group_page_contexts(self):
        adapter = TaskGroupFormAdapter()
        form = object()
        group = object()
        detail_data = SimpleNamespace(group='group-1', tasks=['task-1'])
        add_tasks_data = SimpleNamespace(
            group='group-1',
            available_tasks=['task-2'],
            search='force',
        )

        detail_context = adapter.task_group_detail_context(detail_data)
        create_context = adapter.analog_group_create_context(form)
        update_context = adapter.analog_group_update_context(group, form)
        add_tasks_context = adapter.add_tasks_to_group_context(add_tasks_data)

        self.assertEqual(detail_context['analoggroup'], 'group-1')
        self.assertEqual(detail_context['tasks'], ['task-1'])
        self.assertIn(TASK_BANK_ROLE_CONTROL, dict(detail_context['bank_role_options']))
        self.assertEqual(create_context, {'form': form})
        self.assertEqual(update_context, {'object': group, 'form': form})
        self.assertEqual(add_tasks_context['group'], 'group-1')
        self.assertEqual(add_tasks_context['available_tasks'], ['task-2'])
        self.assertEqual(add_tasks_context['search'], 'force')
        self.assertEqual(
            add_tasks_context['selected_bank_role'],
            TASK_BANK_ROLE_CONTROL,
        )

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

    def test_builds_work_detail_and_form_contexts(self):
        adapter = WorkFormAdapter()
        form = object()
        formset = object()
        work = object()
        form_data = SimpleNamespace(analog_group_options=['group-option-1'])
        detail = SimpleNamespace(
            work='work-1',
            variants=['variant-1'],
            analog_groups=['group-1'],
            spec_preview=['spec-1'],
            work_print_settings=['work-template-1'],
            remedial_sheet_print_settings=['remedial-template-1'],
            work_document_style_options=['style-1'],
            show_sync_button=True,
        )

        detail_context = adapter.work_detail_context(detail)
        create_context = adapter.work_create_context(form, formset, form_data)
        update_context = adapter.work_update_context(
            work,
            form,
            formset,
            form_data,
        )

        self.assertEqual(detail_context['work'], 'work-1')
        self.assertEqual(detail_context['object'], 'work-1')
        self.assertEqual(detail_context['variants'], ['variant-1'])
        self.assertEqual(detail_context['analog_groups'], ['group-1'])
        self.assertEqual(detail_context['spec_preview'], ['spec-1'])
        self.assertEqual(
            detail_context['work_document_templates'],
            ['work-template-1'],
        )
        self.assertEqual(
            detail_context['remedial_sheet_templates'],
            ['remedial-template-1'],
        )
        self.assertEqual(
            detail_context['work_print_settings'],
            ['work-template-1'],
        )
        self.assertEqual(
            detail_context['remedial_sheet_print_settings'],
            ['remedial-template-1'],
        )
        self.assertTrue(detail_context['show_sync_button'])
        self.assertEqual(create_context['form'], form)
        self.assertEqual(create_context['formset'], formset)
        self.assertEqual(create_context['analog_group_options'], ['group-option-1'])
        self.assertEqual(update_context['object'], work)
        self.assertEqual(update_context['form'], form)
        self.assertEqual(update_context['formset'], formset)

    def test_builds_variant_contexts_with_pagination(self):
        adapter = WorkFormAdapter()
        list_data = SimpleNamespace(variants=['v1', 'v2', 'v3'])
        orphan_list_data = SimpleNamespace(
            variants=['o1', 'o2', 'o3'],
            total_orphans=3,
        )
        detail = SimpleNamespace(
            variant='variant-1',
            variant_tasks=['task-1'],
            total_max_points=5,
        )

        list_context = adapter.variant_list_context(
            list_data,
            QueryDict('page=1'),
            paginate_by=2,
        )
        orphan_context = adapter.orphan_variant_list_context(
            orphan_list_data,
            QueryDict('page=1'),
            paginate_by=2,
        )
        detail_context = adapter.variant_detail_context(detail)

        self.assertEqual(list(list_context['variants']), ['v1', 'v2'])
        self.assertTrue(list_context['is_paginated'])
        self.assertEqual(list(orphan_context['variants']), ['o1', 'o2'])
        self.assertEqual(orphan_context['total_orphans'], 3)
        self.assertEqual(detail_context['variant'], 'variant-1')
        self.assertEqual(detail_context['object'], 'variant-1')
        self.assertEqual(detail_context['variant_tasks'], ['task-1'])
        self.assertEqual(detail_context['total_max_points'], 5)

    def test_builds_variant_delete_and_bulk_delete_contexts(self):
        adapter = WorkFormAdapter()
        delete_info = SimpleNamespace(
            task_count=4,
            has_participations=True,
            participation_count=2,
        )
        bulk_result = SimpleNamespace(deleted_count=3, remaining_count=1)

        delete_context = adapter.variant_delete_context(delete_info)
        payload = adapter.bulk_delete_variants_response_payload(bulk_result)

        self.assertEqual(delete_context['delete_info'], delete_info)
        self.assertEqual(delete_context['task_count'], 4)
        self.assertTrue(delete_context['has_grades'])
        self.assertEqual(delete_context['grade_count'], 2)
        self.assertEqual(
            payload,
            {'success': True, 'deleted': 3, 'remaining': 1},
        )

    def test_builds_compose_variants_context(self):
        form_data = SimpleNamespace(
            work='work-1',
            work_groups=['group-1'],
        )
        form = object()

        context = WorkFormAdapter().compose_variants_context(form_data, form)

        self.assertEqual(context['work'], 'work-1')
        self.assertEqual(context['work_groups'], ['group-1'])
        self.assertEqual(context['form'], form)

    def test_builds_document_rendering_status_and_error_payloads(self):
        adapter = WorkFormAdapter()

        self.assertEqual(
            adapter.render_work_unsupported_renderer_payload('docx'),
            {
                'success': False,
                'error': 'Неподдерживаемый тип рендера: docx',
            },
        )
        self.assertEqual(
            adapter.render_work_error_payload(ValueError('bad')),
            {'success': False, 'error': 'bad'},
        )
        self.assertEqual(
            adapter.render_status_payload(),
            {
                'status': 'ready',
                'message': 'Система готова к рендерингу',
            },
        )
        self.assertEqual(
            adapter.variant_placeholder_response_payload(
                SimpleNamespace(message='Пока не реализовано'),
            ),
            {
                'success': True,
                'message': 'Пока не реализовано',
                'files': [],
            },
        )

    def test_builds_remedial_rendering_error_payloads(self):
        adapter = WorkFormAdapter()

        self.assertEqual(
            adapter.remedial_sheet_error_payload('Ошибка'),
            {'status': 'error', 'message': 'Ошибка'},
        )
        self.assertEqual(
            adapter.remedial_sheet_batch_error_payload('Ошибка'),
            {'success': False, 'error': 'Ошибка'},
        )

    def test_builds_work_specs_from_expanded_formset(self):
        analog_group = SimpleNamespace(pk='group-1')
        formset = SimpleNamespace(
            cleaned_data=[
                {
                    'analog_group': analog_group,
                    'order': 2,
                    'count': 1,
                    'weight': 0,
                    'bank_role_filter': TASK_BANK_ROLE_DEMO,
                    'render_mode': TASK_RENDER_MODE_WITH_FULL_SOLUTION,
                    'is_assessable': False,
                    'blank_cells_after': True,
                    'blank_cells_rows': 8,
                },
                {'DELETE': True, 'analog_group': analog_group},
                {},
            ],
        )

        specs = WorkFormAdapter().work_specs_from_formset(formset, work_id='work-1')

        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].work_id, 'work-1')
        self.assertEqual(specs[0].analog_group_id, 'group-1')
        self.assertEqual(specs[0].order, 2)
        self.assertEqual(specs[0].weight, 1)
        self.assertEqual(specs[0].bank_role_filter, TASK_BANK_ROLE_DEMO)
        self.assertEqual(specs[0].render_mode, TASK_RENDER_MODE_WITH_FULL_SOLUTION)
        self.assertFalse(specs[0].is_assessable)
        self.assertTrue(specs[0].blank_cells_after)
        self.assertEqual(specs[0].blank_cells_rows, 8)

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
                '&document_style=worksheet'
                '&print_settings_id=template-work',
            ),
            work_id='w1',
        )

        self.assertEqual(request.work_id, 'w1')
        self.assertEqual(request.print_settings_id, 'template-work')
        self.assertEqual(request.selected_print_settings_id, 'template-work')
        self.assertEqual(request.options.renderer_type, 'html')
        self.assertEqual(request.options.pdf_format, 'A5')
        self.assertEqual(request.options.answer_type, 'with_short_solutions')
        self.assertTrue(request.options.include_hints)
        self.assertTrue(request.options.include_instructions)
        self.assertEqual(request.options.document_style, WORK_DOCUMENT_STYLE_WORKSHEET)

    def test_builds_render_remedial_sheet_request_from_post(self):
        request = WorkFormAdapter().render_remedial_sheet_request_from_post(
            QueryDict(
                'renderer_type=pdf&format=A4'
                '&answer_type=with_full_solutions'
                '&print_settings_id=template-rno',
            ),
            variant_id='v1',
        )

        self.assertEqual(request.variant_id, 'v1')
        self.assertEqual(request.print_settings_id, 'template-rno')
        self.assertEqual(request.selected_print_settings_id, 'template-rno')
        self.assertEqual(request.options.renderer_type, 'pdf')
        self.assertEqual(request.options.pdf_format, 'A4')
        self.assertEqual(request.options.answer_type, 'with_full_solutions')

    def test_builds_render_remedial_sheet_batch_request_from_post(self):
        request = WorkFormAdapter().render_remedial_sheet_batch_request_from_post(
            QueryDict('renderer_type=html&print_settings_id=template-rno'),
            work_id='w1',
        )

        self.assertEqual(request.work_id, 'w1')
        self.assertEqual(request.print_settings_id, 'template-rno')
        self.assertEqual(request.selected_print_settings_id, 'template-rno')
        self.assertEqual(request.options.renderer_type, 'html')

    def test_render_document_requests_accept_legacy_template_id_post_key(self):
        request = WorkFormAdapter().render_work_document_request_from_post(
            QueryDict('renderer_type=html&template_id=template-work'),
            work_id='w1',
        )

        self.assertEqual(request.print_settings_id, 'template-work')

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
