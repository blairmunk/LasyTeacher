"""Infrastructure helpers for Django report query params."""

from core_logic.use_cases.get_events_status_report import (
    EventsStatusReportRequest,
)
from core_logic.use_cases.get_heatmap_course_overview import (
    HeatmapCourseOverviewRequest,
)
from core_logic.use_cases.get_heatmap_drilldown_overview import (
    HeatmapDrilldownOverviewRequest,
)
from core_logic.use_cases.get_heatmap_overview import HeatmapOverviewRequest
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
from core_logic.use_cases.get_work_analysis_report import WorkAnalysisReportRequest
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

    def heatmap_group_url_params_from_query(self, query):
        group_id = query.get('group')
        return {
            'group_param': f'?group={group_id}' if group_id else '',
            'group_suffix': f'&group={group_id}' if group_id else '',
        }

    def heatmap_overview_request_from_query(self, query):
        params = self.heatmap_params_from_query(query)
        return HeatmapOverviewRequest(group_id=params['group_id'])

    def heatmap_course_overview_request_from_query(self, query, course_id):
        params = self.heatmap_params_from_query(query)
        return HeatmapCourseOverviewRequest(
            course_id=course_id,
            group_id=params['group_id'],
        )

    def heatmap_drilldown_overview_request_from_query(self, query, topic_id):
        params = self.heatmap_params_from_query(query)
        return HeatmapDrilldownOverviewRequest(
            topic_id=topic_id,
            group_id=params['group_id'],
        )

    def heatmap_student_detail_request_from_query(
        self,
        query,
        topic_id,
        student_id,
    ):
        return HeatmapStudentDetailRequest(
            topic_id=topic_id,
            student_id=student_id,
            subtopic_id=query.get('subtopic'),
        )

    def heatmap_subtopic_detail_request_from_query(self, query, subtopic_id):
        return HeatmapSubtopicDetailRequest(
            subtopic_id=subtopic_id,
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
