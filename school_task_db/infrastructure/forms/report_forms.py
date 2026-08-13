"""Infrastructure helpers for Django report query params."""

from datetime import timedelta

from django.utils.dateparse import parse_date

from core_logic.entities.event_performance_report import (
    EventReportNarrative,
    SaveEventReportNarrativeParams,
)
from core_logic.entities.student_digest import (
    StudentDigestOptions,
    StudentDigestRequest,
)
from core_logic.use_cases.get_events_status_report import (
    EventsStatusReportRequest,
)
from core_logic.use_cases.get_heatmap_course_report import (
    HeatmapCourseReportRequest,
)
from core_logic.use_cases.get_heatmap_drilldown_report import (
    HeatmapDrilldownReportRequest,
)
from core_logic.use_cases.get_heatmap_report import HeatmapReportRequest
from core_logic.use_cases.get_heatmap_student_detail import (
    HeatmapStudentDetailRequest,
)
from core_logic.use_cases.get_heatmap_subtopic_detail import (
    HeatmapSubtopicDetailRequest,
)
from core_logic.use_cases.get_journal import JournalRequest
from core_logic.use_cases.get_reports_dashboard import ReportsDashboardRequest
from core_logic.use_cases.get_student_performance_report import (
    StudentPerformanceReportRequest,
)
from core_logic.use_cases.get_student_digest_page import (
    StudentDigestPageRequest,
)
from core_logic.use_cases.get_work_analysis_report import WorkAnalysisReportRequest
from core_logic.use_cases.render_event_performance_report_document import (
    RenderEventPerformanceReportDocumentRequest,
)
from core_logic.use_cases.render_student_digest_document import (
    RenderStudentDigestDocumentRequest,
)
from infrastructure.forms.document_rendering import (
    render_target_from_data,
)
from core_logic.value_objects.report_document_options import (
    EventReportDocumentOptions,
)
from reports import plotly_utils


REPORT_STATUS_CHART_ITEMS = {
    'planned': ('Запланировано', 'rgba(23, 162, 184, 0.75)'),
    'in_progress': ('Выполняется', 'rgba(111, 66, 193, 0.75)'),
    'completed': ('Завершено', 'rgba(40, 167, 69, 0.75)'),
    'reviewing': ('На проверке', 'rgba(255, 193, 7, 0.75)'),
    'graded': ('Проверено', 'rgba(13, 110, 253, 0.75)'),
    'closed': ('Закрыто', 'rgba(108, 117, 125, 0.75)'),
}


class ReportFormAdapter:
    def event_report_narrative_params(self, event_id, data):
        return SaveEventReportNarrativeParams(
            event_id=str(event_id),
            narrative=EventReportNarrative(
                possible_causes=data.get('possible_causes', '').strip(),
                recommendations=data.get('recommendations', '').strip(),
                planned_actions=data.get('planned_actions', '').strip(),
                additional_notes=data.get('additional_notes', '').strip(),
            ),
        )

    def student_digest_request_from_query(self, query, year, today):
        submitted = query.get('apply') == '1'
        start_date = parse_date(query.get('start_date', ''))
        end_date = parse_date(query.get('end_date', ''))
        if not submitted:
            end_date = today
            start_date = today - timedelta(days=7)

        try:
            threshold = int(query.get('retake_score_threshold', 2))
        except (TypeError, ValueError):
            threshold = 2
        threshold = min(4, max(1, threshold))

        def enabled(name, default=True):
            return name in query if submitted else default

        return StudentDigestRequest(
            group_id=query.get('group', ''),
            student_id=query.get('student', ''),
            start_date=start_date,
            end_date=end_date,
            year=year,
            options=StudentDigestOptions(
                include_summary=enabled('include_summary'),
                include_details=enabled('include_details'),
                include_focus=enabled('include_focus'),
                include_retakes=enabled('include_retakes'),
                include_teacher_comments=enabled(
                    'include_teacher_comments',
                    default=False,
                ),
                include_task_comments=enabled(
                    'include_task_comments',
                    default=False,
                ),
                include_absences=enabled('include_absences'),
                retake_score_threshold=threshold,
            ),
        )

    def student_digest_page_request_from_query(self, query, year, today):
        return StudentDigestPageRequest(
            digest_request=self.student_digest_request_from_query(
                query,
                year=year,
                today=today,
            ),
            fallback_end_date=today,
        )

    def event_report_document_request(self, event_id, data):
        options_submitted = data.get('report_options_submitted') == '1'
        def enabled(name, default=True):
            return name in data if options_submitted else default

        return RenderEventPerformanceReportDocumentRequest(
            event_id=str(event_id),
            render_target=render_target_from_data(data),
            presentation_profile_id=data.get(
                'presentation_profile_id',
                '',
            ).strip(),
            options=EventReportDocumentOptions(
                include_specification=enabled('include_specification'),
                include_summary=enabled('include_summary'),
                include_task_analysis=enabled('include_task_analysis'),
                include_conclusions=enabled('include_conclusions'),
                include_content_element_text=enabled(
                    'include_content_element_text',
                ),
                include_teacher_notes=enabled(
                    'include_teacher_notes',
                    default=False,
                ),
            ),
        )

    def student_digest_document_request(self, data, year, today):
        return RenderStudentDigestDocumentRequest(
            digest_request=self.student_digest_request_from_query(
                data,
                year=year,
                today=today,
            ),
            render_target=render_target_from_data(data),
            presentation_profile_id=data.get(
                'presentation_profile_id',
                '',
            ).strip(),
        )

    def reports_dashboard_request(self, year=None, current_date=None):
        return ReportsDashboardRequest(
            year=year,
            current_date=current_date,
        )

    def reports_dashboard_context(self, report):
        context = {
            'total_students': report.total_students,
            'total_events': report.total_events,
            'total_works': report.total_works,
            'total_courses': report.total_courses,
            'total_marks': report.total_marks,
            'average_score': report.average_score,
            'marks_last_month': report.marks_last_month,
            'events_planned': report.events_planned,
            'events_completed': report.events_completed,
            'events_graded': report.events_graded,
            'class_stats': report.class_stats,
            'recent_events': report.recent_events,
            'courses': report.courses,
            'active_report': report.active_report,
            'active_course_pk': report.active_course_pk,
        }
        context.update(self.reports_dashboard_chart_context(report))
        return context

    def reports_dashboard_chart_context(self, report):
        status_labels, status_values, status_colors = (
            self._event_status_chart_data(report.event_status_counts)
        )
        return {
            'score_chart_json': plotly_utils.to_json(
                plotly_utils.score_distribution_config(report.score_counts),
            ),
            'activity_chart_json': plotly_utils.to_json(
                plotly_utils.line_chart_config(
                    report.monthly_labels,
                    report.monthly_values,
                    title='Активность по месяцам',
                ),
            ),
            'class_chart_json': plotly_utils.to_json(
                plotly_utils.multi_bar_config(
                    report.class_names,
                    {
                        'Средний балл': report.class_avg_scores,
                        '% выполнения (÷25)': [
                            round(c / 25, 2)
                            for c in report.class_completion
                        ],
                    },
                    title='Сравнение классов',
                ),
            ),
            'gauge_json': plotly_utils.to_json(
                plotly_utils.gauge_config(
                    report.average_score or 0,
                    title='Средний балл',
                ),
            ),
            'donut_json': plotly_utils.to_json(
                plotly_utils.donut_config(
                    status_labels,
                    status_values,
                    title='Статусы событий',
                    colors=status_colors,
                ),
            ),
            'box_plot_json': plotly_utils.to_json(
                plotly_utils.box_plot_config(
                    report.box_data,
                    title='Распределение по работам',
                ),
            ),
        }

    def student_performance_request_from_query(self, query, year=None):
        return StudentPerformanceReportRequest(
            year=year,
            group_id=query.get('group'),
        )

    def work_analysis_request(self, year=None):
        return WorkAnalysisReportRequest(year=year)

    def events_status_request(self, year=None, current_date=None):
        return EventsStatusReportRequest(
            year=year,
            current_date=current_date,
        )

    def heatmap_params_from_query(self, query):
        return {
            'group_id': query.get('group'),
            'section': query.get('section', ''),
            'transpose': query.get('transpose') == '1',
        }

    def heatmap_report_request_from_query(self, query):
        params = self.heatmap_params_from_query(query)
        return HeatmapReportRequest(
            group_id=params['group_id'],
            section_filter=params['section'],
        )

    def heatmap_course_report_request_from_query(self, query, course_id):
        params = self.heatmap_params_from_query(query)
        return HeatmapCourseReportRequest(
            course_id=str(course_id),
            group_id=params['group_id'],
        )

    def heatmap_drilldown_report_request_from_query(self, query, topic_id):
        params = self.heatmap_params_from_query(query)
        return HeatmapDrilldownReportRequest(
            topic_id=str(topic_id),
            group_id=params['group_id'],
        )

    def heatmap_student_detail_request_from_query(
        self,
        query,
        topic_id,
        student_id,
    ):
        return HeatmapStudentDetailRequest(
            topic_id=str(topic_id),
            student_id=str(student_id),
            subtopic_id=query.get('subtopic'),
        )

    def heatmap_subtopic_detail_request_from_query(self, query, subtopic_id):
        return HeatmapSubtopicDetailRequest(
            subtopic_id=str(subtopic_id),
            group_id=query.get('group'),
        )

    def journal_request_from_query(self, query, course_id, group_id, year=None):
        return JournalRequest(
            course_id=course_id,
            group_id=group_id,
            year=year,
            show_debts_only=query.get('debts') == '1',
        )

    def _event_status_chart_data(self, event_status_counts):
        labels = []
        values = []
        colors = []
        for status_code, (label, color) in REPORT_STATUS_CHART_ITEMS.items():
            count = event_status_counts.get(status_code, 0)
            if count > 0:
                labels.append(label)
                values.append(count)
                colors.append(color)
        return labels, values, colors
