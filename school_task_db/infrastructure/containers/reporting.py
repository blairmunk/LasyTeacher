"""Reporting subsystem wiring for the application dependency container."""

from core_logic.use_cases.get_event_performance_report import (
    GetEventPerformanceReportUseCase,
)
from core_logic.use_cases.get_events_status_report import (
    GetEventsStatusReportUseCase,
)
from core_logic.use_cases.get_heatmap_course_overview import (
    GetHeatmapCourseOverviewUseCase,
)
from core_logic.use_cases.get_heatmap_course_report import (
    GetHeatmapCourseReportUseCase,
)
from core_logic.use_cases.get_heatmap_course_timeline import (
    GetHeatmapCourseTimelineUseCase,
)
from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    GetHeatmapCourseTopicMatrixUseCase,
)
from core_logic.use_cases.get_heatmap_drilldown_overview import (
    GetHeatmapDrilldownOverviewUseCase,
)
from core_logic.use_cases.get_heatmap_drilldown_report import (
    GetHeatmapDrilldownReportUseCase,
)
from core_logic.use_cases.get_heatmap_overview import GetHeatmapOverviewUseCase
from core_logic.use_cases.get_heatmap_report import GetHeatmapReportUseCase
from core_logic.use_cases.get_heatmap_student_detail import (
    GetHeatmapStudentDetailUseCase,
)
from core_logic.use_cases.get_heatmap_subtopic_detail import (
    GetHeatmapSubtopicDetailUseCase,
)
from core_logic.use_cases.get_heatmap_subtopic_matrix import (
    GetHeatmapSubtopicMatrixUseCase,
)
from core_logic.use_cases.get_heatmap_topic_matrix import (
    GetHeatmapTopicMatrixUseCase,
)
from core_logic.use_cases.get_journal import GetJournalUseCase
from core_logic.use_cases.get_journal_select import GetJournalSelectUseCase
from core_logic.use_cases.get_reports_dashboard import GetReportsDashboardUseCase
from core_logic.use_cases.get_student_digest_page import (
    GetStudentDigestPageUseCase,
)
from core_logic.use_cases.get_student_digests import GetStudentDigestsUseCase
from core_logic.use_cases.get_student_performance_report import (
    GetStudentPerformanceReportUseCase,
)
from core_logic.use_cases.get_work_analysis_report import (
    GetWorkAnalysisReportUseCase,
)
from core_logic.use_cases.save_event_report_narrative import (
    SaveEventReportNarrativeUseCase,
)
from infrastructure.forms.report_forms import ReportFormAdapter
from infrastructure.presenters.heatmap import HeatmapPresenter
from infrastructure.repositories.django_event_performance_report_query_repo import (
    DjangoEventPerformanceReportQueryRepository,
)
from infrastructure.repositories.django_event_report_narrative_command_repo import (
    DjangoEventReportNarrativeCommandRepository,
)
from infrastructure.repositories.django_events_status_repo import (
    DjangoEventsStatusRepository,
)
from infrastructure.repositories.django_heatmap_detail_repo import (
    DjangoHeatmapDetailRepository,
)
from infrastructure.repositories.django_heatmap_matrix_repo import (
    DjangoHeatmapMatrixRepository,
)
from infrastructure.repositories.django_heatmap_overview_repo import (
    DjangoHeatmapOverviewRepository,
)
from infrastructure.repositories.django_journal_catalog_repo import (
    DjangoJournalCatalogRepository,
)
from infrastructure.repositories.django_journal_report_repo import (
    DjangoJournalReportRepository,
)
from infrastructure.repositories.django_reports_dashboard_repo import (
    DjangoReportsDashboardRepository,
)
from infrastructure.repositories.django_student_digest_repo import (
    DjangoStudentDigestRepository,
)
from infrastructure.repositories.django_student_performance_repo import (
    DjangoStudentPerformanceRepository,
)
from infrastructure.repositories.django_work_analysis_repo import (
    DjangoWorkAnalysisRepository,
)


class ReportingCompositionMixin:
    """Owns read-side reporting and analytics infrastructure wiring."""

    def _initialize_reporting_composition(self):
        self._events_status_repo = None
        self._reports_dashboard_repo = None
        self._student_performance_repo = None
        self._work_analysis_repo = None
        self._heatmap_detail_repo = None
        self._heatmap_matrix_repo = None
        self._heatmap_overview_repo = None
        self._journal_catalog_repo = None
        self._journal_report_repo = None
        self._event_performance_report_query_repo = None
        self._event_report_narrative_command_repo = None
        self._student_digest_repo = None
        self._report_form_adapter = None
        self._heatmap_presenter = None

    @property
    def events_status_repo(self):
        if self._events_status_repo is None:
            self._events_status_repo = DjangoEventsStatusRepository()
        return self._events_status_repo

    @property
    def reports_dashboard_repo(self):
        if self._reports_dashboard_repo is None:
            self._reports_dashboard_repo = DjangoReportsDashboardRepository()
        return self._reports_dashboard_repo

    @property
    def student_performance_repo(self):
        if self._student_performance_repo is None:
            self._student_performance_repo = (
                DjangoStudentPerformanceRepository()
            )
        return self._student_performance_repo

    @property
    def work_analysis_repo(self):
        if self._work_analysis_repo is None:
            self._work_analysis_repo = DjangoWorkAnalysisRepository()
        return self._work_analysis_repo

    @property
    def heatmap_detail_repo(self):
        if self._heatmap_detail_repo is None:
            self._heatmap_detail_repo = DjangoHeatmapDetailRepository()
        return self._heatmap_detail_repo

    @property
    def heatmap_matrix_repo(self):
        if self._heatmap_matrix_repo is None:
            self._heatmap_matrix_repo = DjangoHeatmapMatrixRepository()
        return self._heatmap_matrix_repo

    @property
    def heatmap_overview_repo(self):
        if self._heatmap_overview_repo is None:
            self._heatmap_overview_repo = DjangoHeatmapOverviewRepository()
        return self._heatmap_overview_repo

    @property
    def journal_catalog_repo(self):
        if self._journal_catalog_repo is None:
            self._journal_catalog_repo = DjangoJournalCatalogRepository()
        return self._journal_catalog_repo

    @property
    def journal_report_repo(self):
        if self._journal_report_repo is None:
            self._journal_report_repo = DjangoJournalReportRepository()
        return self._journal_report_repo

    @property
    def event_performance_report_query_repo(self):
        if self._event_performance_report_query_repo is None:
            self._event_performance_report_query_repo = (
                DjangoEventPerformanceReportQueryRepository()
            )
        return self._event_performance_report_query_repo

    @property
    def event_report_narrative_command_repo(self):
        if self._event_report_narrative_command_repo is None:
            self._event_report_narrative_command_repo = (
                DjangoEventReportNarrativeCommandRepository()
            )
        return self._event_report_narrative_command_repo

    @property
    def student_digest_repo(self):
        if self._student_digest_repo is None:
            self._student_digest_repo = DjangoStudentDigestRepository()
        return self._student_digest_repo

    @property
    def report_form_adapter(self):
        if self._report_form_adapter is None:
            self._report_form_adapter = ReportFormAdapter()
        return self._report_form_adapter

    @property
    def heatmap_presenter(self):
        if self._heatmap_presenter is None:
            self._heatmap_presenter = HeatmapPresenter()
        return self._heatmap_presenter

    def get_events_status_report_use_case(self):
        return GetEventsStatusReportUseCase(
            report_repo=self.events_status_repo,
        )

    def get_event_performance_report_use_case(self):
        return GetEventPerformanceReportUseCase(
            report_repo=self.event_performance_report_query_repo,
        )

    def save_event_report_narrative_use_case(self):
        return SaveEventReportNarrativeUseCase(
            report_repo=self.event_report_narrative_command_repo,
        )

    def get_student_digests_use_case(self):
        return GetStudentDigestsUseCase(
            digest_repo=self.student_digest_repo,
        )

    def get_student_digest_page_use_case(self):
        return GetStudentDigestPageUseCase(
            get_student_digests_use_case=self.get_student_digests_use_case(),
        )

    def get_reports_dashboard_use_case(self):
        return GetReportsDashboardUseCase(
            report_repo=self.reports_dashboard_repo,
        )

    def get_heatmap_overview_use_case(self):
        return GetHeatmapOverviewUseCase(
            report_repo=self.heatmap_overview_repo,
        )

    def get_heatmap_course_overview_use_case(self):
        return GetHeatmapCourseOverviewUseCase(
            report_repo=self.heatmap_overview_repo,
        )

    def get_heatmap_course_report_use_case(self):
        return GetHeatmapCourseReportUseCase(
            overview_use_case=self.get_heatmap_course_overview_use_case(),
            matrix_use_case=self.get_heatmap_course_topic_matrix_use_case(),
            timeline_use_case=self.get_heatmap_course_timeline_use_case(),
        )

    def get_heatmap_course_topic_matrix_use_case(self):
        return GetHeatmapCourseTopicMatrixUseCase(
            report_repo=self.heatmap_matrix_repo,
        )

    def get_heatmap_course_timeline_use_case(self):
        return GetHeatmapCourseTimelineUseCase(
            report_repo=self.heatmap_matrix_repo,
        )

    def get_heatmap_drilldown_overview_use_case(self):
        return GetHeatmapDrilldownOverviewUseCase(
            report_repo=self.heatmap_overview_repo,
        )

    def get_heatmap_drilldown_report_use_case(self):
        return GetHeatmapDrilldownReportUseCase(
            overview_use_case=self.get_heatmap_drilldown_overview_use_case(),
            matrix_use_case=self.get_heatmap_subtopic_matrix_use_case(),
        )

    def get_heatmap_student_detail_use_case(self):
        return GetHeatmapStudentDetailUseCase(
            report_repo=self.heatmap_detail_repo,
        )

    def get_heatmap_subtopic_detail_use_case(self):
        return GetHeatmapSubtopicDetailUseCase(
            report_repo=self.heatmap_detail_repo,
        )

    def get_heatmap_subtopic_matrix_use_case(self):
        return GetHeatmapSubtopicMatrixUseCase(
            report_repo=self.heatmap_matrix_repo,
        )

    def get_heatmap_topic_matrix_use_case(self):
        return GetHeatmapTopicMatrixUseCase(
            report_repo=self.heatmap_matrix_repo,
        )

    def get_heatmap_report_use_case(self):
        return GetHeatmapReportUseCase(
            overview_use_case=self.get_heatmap_overview_use_case(),
            matrix_use_case=self.get_heatmap_topic_matrix_use_case(),
        )

    def get_work_analysis_report_use_case(self):
        return GetWorkAnalysisReportUseCase(
            report_repo=self.work_analysis_repo,
        )

    def get_student_performance_report_use_case(self):
        return GetStudentPerformanceReportUseCase(
            report_repo=self.student_performance_repo,
        )

    def get_journal_select_use_case(self):
        return GetJournalSelectUseCase(
            report_repo=self.journal_catalog_repo,
        )

    def get_journal_use_case(self):
        return GetJournalUseCase(
            report_repo=self.journal_report_repo,
        )
