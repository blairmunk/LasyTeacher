# reports/views.py

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone

from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    HeatmapCourseTopicMatrixRequest,
)
from core_logic.use_cases.get_heatmap_course_timeline import (
    HeatmapCourseTimelineRequest,
)
from core_logic.use_cases.get_heatmap_subtopic_matrix import (
    HeatmapSubtopicMatrixRequest,
)
from core_logic.use_cases.get_heatmap_topic_matrix import (
    HeatmapTopicMatrixRequest,
)
from core_logic.use_cases.get_journal_select import JournalSelectRequest
from core_logic.use_cases.get_presentation_profile_list import (
    GetPresentationProfileListRequest,
)
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileRequest,
)
from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    STUDENT_DIGEST_DOCUMENT_TYPE,
)
from infrastructure.container import container


class ReportsDashboardView(TemplateView):
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = container.get_reports_dashboard_use_case().execute(
            container.report_form_adapter.reports_dashboard_request(
                year=getattr(self.request, 'current_year', None),
                current_date=timezone.now(),
            ),
        )
        context.update(
            container.report_form_adapter.reports_dashboard_context(report),
        )
        return context


class StudentPerformanceView(TemplateView):
    """Отчет по успеваемости учеников"""
    template_name = 'reports/student_performance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = container.get_student_performance_report_use_case().execute(
            container.report_form_adapter.student_performance_request_from_query(
                self.request.GET,
                year=getattr(self.request, 'current_year', None),
            ),
        )

        context.update({
            'students_stats': report.students_stats,
            'groups': report.groups,
            'selected_group': report.selected_group,
            'summary_stats': report.summary_stats,
            'active_report': report.active_report,
            'active_course_pk': report.active_course_pk,
            'courses': report.courses,
        })
        return context


class WorkAnalysisView(TemplateView):
    """Анализ работ и их результатов"""
    template_name = 'reports/work_analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = container.get_work_analysis_report_use_case().execute(
            container.report_form_adapter.work_analysis_request(
                year=getattr(self.request, 'current_year', None),
            ),
        )

        context.update({
            'works_analysis': report.works_analysis,
            'summary_stats': report.summary_stats,
            'active_report': report.active_report,
            'active_course_pk': report.active_course_pk,
            'courses': report.courses,
        })
        return context


class EventsStatusView(TemplateView):
    """Отчет по статусам событий"""
    template_name = 'reports/events_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = container.get_events_status_report_use_case().execute(
            container.report_form_adapter.events_status_request(
                year=getattr(self.request, 'current_year', None),
                current_date=timezone.now(),
            ),
        )

        context.update({
            'events_by_status': report.events_by_status,
            'overdue_events': report.overdue_events,
            'long_reviewing': report.long_reviewing,
            'completed_unchecked': report.completed_unchecked,
            'participation_stats': report.participation_stats,
            'all_events': report.all_events,
            'active_report': report.active_report,
            'active_course_pk': report.active_course_pk,
            'courses': report.courses,
        })

        return context


class EventPerformanceReportView(View):
    template_name = 'reports/event_performance_report.html'

    def get(self, request, event_pk):
        report = container.get_event_performance_report_use_case().execute(
            str(event_pk),
        )
        if report is None:
            raise Http404('Событие не найдено.')
        profiles = container.get_presentation_profile_list_use_case().execute(
            GetPresentationProfileListRequest(
                document_type=EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
            ),
        )
        return render(request, self.template_name, {
            'report': report,
            'presentation_profiles': profiles.presentation_profiles,
            'active_report': 'event-performance',
        })

    def post(self, request, event_pk):
        result = container.save_event_report_narrative_use_case().execute(
            container.report_form_adapter.event_report_narrative_params(
                event_pk,
                request.POST,
            ),
        )
        if result.status == 'not_found':
            raise Http404('Событие не найдено.')
        messages.success(request, 'Текстовые разделы отчёта сохранены.')
        return redirect('reports:event-performance', event_pk=event_pk)


class EventPerformanceReportDocumentView(View):
    def post(self, request, event_pk):
        result = (
            container
            .render_event_performance_report_document_use_case()
            .execute(
                container.report_form_adapter.event_report_document_request(
                    event_pk,
                    request.POST,
                ),
            )
        )
        presentation = (
            container.report_document_web_presenter.event_report(result)
        )
        if presentation.is_not_found:
            raise Http404(presentation.not_found_message)
        response = _rendered_document_response(presentation)
        if response is not None:
            return response
        messages.error(request, presentation.error_message)
        return redirect('reports:event-performance', event_pk=event_pk)


class StudentDigestView(View):
    template_name = 'reports/student_digests.html'

    def get(self, request):
        digest_request = (
            container.report_form_adapter.student_digest_request_from_query(
                request.GET,
                year=getattr(request, 'current_year', None),
                today=timezone.localdate(),
            )
        )
        form_error = ''
        try:
            page = container.get_student_digests_use_case().execute(
                digest_request,
            )
        except ValueError as error:
            form_error = str(error)
            fallback_request = (
                container.report_form_adapter.student_digest_request_from_query(
                    {},
                    year=getattr(request, 'current_year', None),
                    today=timezone.localdate(),
                )
            )
            page = container.get_student_digests_use_case().execute(
                fallback_request,
            )
        profiles = container.get_presentation_profile_list_use_case().execute(
            GetPresentationProfileListRequest(
                document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
            ),
        )
        return render(request, self.template_name, {
            'page': page,
            'presentation_profiles': profiles.presentation_profiles,
            'form_error': form_error,
            'active_report': page.active_report,
        })


class StudentDigestDocumentView(View):
    def post(self, request):
        document_request = (
            container.report_form_adapter.student_digest_document_request(
                request.POST,
                year=getattr(request, 'current_year', None),
                today=timezone.localdate(),
            )
        )
        try:
            result = container.render_student_digest_document_use_case().execute(
                document_request,
            )
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('reports:student-digests')
        presentation = (
            container.report_document_web_presenter.student_digest(result)
        )
        if presentation.is_not_found:
            raise Http404(presentation.not_found_message)
        response = _rendered_document_response(presentation)
        if response is not None:
            return response
        messages.error(request, presentation.error_message)
        return redirect('reports:student-digests')


def _rendered_document_response(presentation):
    if not presentation.has_file:
        return None
    generated = container.get_rendered_document_file_use_case().execute(
        GetRenderedDocumentFileRequest(
            file_type=presentation.file_type,
            filename=presentation.filename,
        ),
    )
    return container.rendered_document_file_presenter.response(
        generated,
        disposition='inline',
    )



# ============================================================
# HEATMAP
# ============================================================


class HeatmapView(View):
    """Тепловая карта: ученики x темы"""

    def get(self, request):
        params = container.report_form_adapter.heatmap_params_from_query(
            request.GET,
        )
        section = params['section']
        transpose = params['transpose']
        overview = container.get_heatmap_overview_use_case().execute(
            container.report_form_adapter.heatmap_overview_request_from_query(
                request.GET,
            ),
        )

        groups = overview.groups
        group = overview.selected_group
        students = overview.students

        if not students:
            return render(request, 'reports/heatmap.html', {
                'groups': groups, 'selected_group': group,
                'sections': overview.sections, 'selected_section': section,
                'has_data': False, 'is_transposed': transpose,
                'active_report': overview.active_report,
                'active_course_pk': overview.active_course_pk,
                'courses': overview.courses,
            })

        matrix = container.get_heatmap_topic_matrix_use_case().execute(
            HeatmapTopicMatrixRequest(
                student_ids=[student.pk for student in students],
                section_filter=section,
            ),
        )
        matrix_context = (
            container.heatmap_presenter.heatmap_topic_matrix_context(
                matrix,
                transpose=transpose,
                group_id=str(group.pk) if group else '',
            )
        )

        return render(request, 'reports/heatmap.html', {
            'groups': groups,
            'selected_group': group,
            'sections': overview.sections,
            'selected_section': section,
            'is_transposed': transpose,
            'toggle_url': (
                container.heatmap_presenter.heatmap_toggle_url(request.GET)
            ),
            **matrix_context,
            'total_students': len(students),
            'total_topics': len(matrix.columns),
            'active_report': overview.active_report,
            'active_course_pk': overview.active_course_pk,
            'courses': overview.courses,
        })

class HeatmapCourseView(View):
    """Тепловая карта по курсу: ученики × темы курса"""

    def get(self, request, course_pk):
        params = container.report_form_adapter.heatmap_params_from_query(
            request.GET,
        )
        transpose = params['transpose']
        overview = container.get_heatmap_course_overview_use_case().execute(
            container.report_form_adapter.heatmap_course_overview_request_from_query(
                request.GET,
                course_id=course_pk,
            ),
        )
        course = overview.course
        course_groups = overview.groups
        group = overview.selected_group
        students = overview.students
        student_ids = [student.pk for student in students]
        work_ids = [work.pk for work in overview.course_works]

        if not students:
            return render(request, 'reports/heatmap_course.html', {
                'course': course,
                'groups': course_groups,
                'selected_group': group,
                'has_data': False,
                'is_transposed': transpose,
                'active_report': overview.active_report,
                'active_course_pk': overview.active_course_pk,
                'courses': overview.courses,
            })

        matrix = container.get_heatmap_course_topic_matrix_use_case().execute(
            HeatmapCourseTopicMatrixRequest(
                student_ids=student_ids,
                work_ids=work_ids,
            ),
        )
        matrix_context = (
            container.heatmap_presenter.heatmap_topic_matrix_context(
                matrix,
                transpose=transpose,
                group_id=str(group.pk) if group else '',
            )
        )

        timeline = container.get_heatmap_course_timeline_use_case().execute(
            HeatmapCourseTimelineRequest(
                student_ids=student_ids,
                work_ids=work_ids,
            ),
        )
        timeline_json = (
            container.heatmap_presenter.heatmap_course_timeline_json(
                timeline,
            )
        )

        return render(request, 'reports/heatmap_course.html', {
            'course': course,
            'groups': course_groups,
            'selected_group': group,
            'is_transposed': transpose,
            'toggle_url': container.heatmap_presenter.heatmap_toggle_url(
                request.GET,
                path=request.path,
            ),
            **matrix_context,
            'total_students': len(students),
            'total_topics': len(matrix.columns),
            'timeline_json': timeline_json,
            'active_report': overview.active_report,
            'active_course_pk': overview.active_course_pk,
            'courses': overview.courses,
        })


class HeatmapDrilldownView(View):
    """Drill-down: ученики x подтемы одной темы"""

    def get(self, request, topic_pk):
        params = container.report_form_adapter.heatmap_params_from_query(
            request.GET,
        )
        transpose = params['transpose']
        overview = container.get_heatmap_drilldown_overview_use_case().execute(
            container.report_form_adapter.heatmap_drilldown_overview_request_from_query(
                request.GET,
                topic_id=topic_pk,
            ),
        )

        topic = overview.topic
        groups = overview.groups
        group = overview.selected_group
        students = overview.students
        matrix = container.get_heatmap_subtopic_matrix_use_case().execute(
            HeatmapSubtopicMatrixRequest(
                student_ids=[student.pk for student in students],
                topic_id=topic_pk,
            ),
        )
        matrix_context = (
            container.heatmap_presenter.heatmap_subtopic_matrix_context(
                matrix,
                topic_id=topic.pk,
                transpose=transpose,
                group_id=str(group.pk) if group else '',
            )
        )

        return render(request, 'reports/heatmap_drilldown.html', {
            'topic': topic,
            'groups': groups,
            'selected_group': group,
            'is_transposed': transpose,
            'toggle_url': container.heatmap_presenter.heatmap_toggle_url(
                request.GET,
                path=request.path,
            ),
            **matrix_context,
            'active_report': overview.active_report,
            'active_course_pk': overview.active_course_pk,
            'courses': overview.courses,
        })


class HeatmapStudentView(View):
    """Детальный вид: один ученик × подтемы одной темы"""

    def get(self, request, topic_pk, student_pk):
        group_params = (
            container.heatmap_presenter.heatmap_group_url_params_from_query(
                request.GET,
            )
        )
        detail = container.get_heatmap_student_detail_use_case().execute(
            container.report_form_adapter.heatmap_student_detail_request_from_query(
                request.GET,
                topic_id=topic_pk,
                student_id=student_pk,
            ),
        )

        return render(request, 'reports/heatmap_student.html', {
            'topic': detail.topic,
            'student': detail.student,
            'details': detail.details,
            'subtopic_summary': detail.subtopic_summary,
            'selected_subtopic': detail.selected_subtopic,
            'group_param': group_params['group_param'],
            'group_suffix': group_params['group_suffix'],
            'active_report': detail.active_report,
            'active_course_pk': detail.active_course_pk,
            'courses': detail.courses,
        })


class HeatmapSubtopicView(View):
    """Анализ подтемы: все ученики × задания одной подтемы"""

    def get(self, request, subtopic_pk):
        detail = container.get_heatmap_subtopic_detail_use_case().execute(
            container.report_form_adapter.heatmap_subtopic_detail_request_from_query(
                request.GET,
                subtopic_id=subtopic_pk,
            ),
        )
        student_rows_context = (
            container.heatmap_presenter.heatmap_subtopic_student_rows(
                detail,
            )
        )

        return render(request, 'reports/heatmap_subtopic.html', {
            'subtopic': detail.subtopic,
            'topic': detail.topic,
            'groups': detail.groups,
            'selected_group': detail.selected_group,
            **student_rows_context,
            'task_rows': detail.task_rows,
            'overall_pct': detail.overall_pct,
            'overall_css': detail.overall_css,
            'total_students': detail.total_students,
            'students_with_data': detail.students_with_data,
            'active_report': detail.active_report,
            'active_course_pk': detail.active_course_pk,
            'courses': detail.courses,
        })


class JournalSelectView(TemplateView):
    """Выбор курса и класса для журнала"""
    template_name = 'reports/journal_select.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = getattr(self.request, 'current_year', None)
        journal = container.get_journal_select_use_case().execute(
            JournalSelectRequest(year=year),
        )
        context.update({
            'journal_links': journal.journal_links,
            'courses': journal.courses,
            'groups': journal.groups,
            'active_report': journal.active_report,
            'active_course_pk': journal.active_course_pk,
        })
        return context


class JournalView(TemplateView):
    """Классный журнал — ученики × события"""
    template_name = 'reports/journal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        journal = container.get_journal_use_case().execute(
            container.report_form_adapter.journal_request_from_query(
                self.request.GET,
                course_id=kwargs['course_pk'],
                group_id=kwargs['group_pk'],
                year=getattr(self.request, 'current_year', None),
            ),
        )

        context.update({
            'course': journal.course,
            'group': journal.group,
            'events': journal.events,
            'event_stats': journal.event_stats,
            'rows': journal.rows,
            'all_rows_count': journal.all_rows_count,
            'show_debts_only': journal.show_debts_only,
            'total_debts': journal.total_debts,
            'students_with_debts': journal.students_with_debts,
            'active_report': journal.active_report,
            'active_course_pk': journal.active_course_pk,
            'courses': journal.courses,
        })
        return context

# ============================================================
# ТЕХНИЧЕСКИЕ ОТЧЁТЫ (здоровье базы заданий)
# ============================================================

class TaskDBHealthView(TemplateView):
    """Здоровье базы заданий"""
    template_name = 'reports/db_health.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        health = container.get_task_db_health_use_case().execute()

        context.update({
            'stats': health.stats,
            'orphan_variants': health.orphan_variants,
            'empty_groups': health.empty_groups,
            'coverage_issues': health.coverage_issues,
            'difficulty_dist': health.difficulty_dist,
            'ungrouped_tasks': health.ungrouped_tasks,
            'fragile_groups': health.fragile_groups,
            'works_no_variants': health.works_no_variants,
            'works_no_spec': health.works_no_spec,
            'type_dist': health.type_dist,
            'most_used_tasks': health.most_used_tasks,
            'group_sizes': health.group_sizes,
            'unverified_tasks': health.unverified_tasks,
            'no_source_tasks': health.no_source_tasks,
            'no_grade_tasks': health.no_grade_tasks,
            'health': health.health,
            'active_report': health.active_report,
            'active_course_pk': health.active_course_pk,
            'courses': health.courses,
        })
        return context
