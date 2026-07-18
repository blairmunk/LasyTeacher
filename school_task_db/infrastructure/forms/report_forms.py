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


class ReportFormAdapter:
    def reports_dashboard_request(self, year=None, current_date=None):
        return ReportsDashboardRequest(
            year=year,
            current_date=current_date,
        )

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
