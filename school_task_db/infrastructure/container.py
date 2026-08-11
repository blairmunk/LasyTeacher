"""Small dependency container for application use cases."""

from core_logic.services.analytics_service import StudentAnalyticsService
from core_logic.services.event_service import EventService
from core_logic.services.grading_service import GradingService
from core_logic.services.remedial_service import RemedialService
from core_logic.services.review_service import ReviewService
from core_logic.services.work_service import WorkService
from core_logic.use_cases.add_event_participants import AddEventParticipantsUseCase
from core_logic.use_cases.analyze_task_images import (
    AnalyzeTaskImagesUseCase,
    ApplyTaskImagePositionSuggestionsUseCase,
)
from core_logic.use_cases.activate_academic_year import (
    ActivateAcademicYearUseCase,
)
from core_logic.use_cases.assign_event_variants import AssignEventVariantsUseCase
from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantUseCase,
)
from core_logic.use_cases.bulk_delete_variants import BulkDeleteVariantsUseCase
from core_logic.use_cases.bulk_change_task_groups import (
    BulkAddTasksToGroupUseCase,
    BulkCreateGroupFromTasksUseCase,
    BulkRemoveTasksFromGroupsUseCase,
)
from core_logic.use_cases.calculate_review_score import CalculateReviewScoreUseCase
from core_logic.use_cases.change_event_status import ChangeEventStatusUseCase
from core_logic.use_cases.change_task_group_membership import (
    AddTasksToGroupUseCase,
    RemoveTaskFromGroupUseCase,
    UpdateTaskGroupRolesUseCase,
)
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
)
from core_logic.use_cases.create_source import CreateSourceUseCase
from core_logic.use_cases.create_student_remedial_variant import (
    CreateStudentRemedialVariantUseCase,
)
from core_logic.use_cases.create_remedial_wizard_work import (
    CreateRemedialWizardWorkUseCase,
)
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansUseCase,
)
from core_logic.use_cases.create_work_from_groups import (
    PrepareCreateWorkFromGroupsSubmissionUseCase,
    CreateWorkFromGroupsUseCase,
)
from core_logic.use_cases.create_work_from_tasks import CreateWorkFromTasksUseCase
from core_logic.use_cases.delete_variant import DeleteVariantUseCase
from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsUseCase
from core_logic.use_cases.delete_task import DeleteTaskUseCase
from core_logic.use_cases.finalize_review_event import FinalizeReviewEventUseCase
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase
from core_logic.use_cases.execute_task_import_submission import (
    ExecuteTaskImportSubmissionUseCase,
)
from core_logic.use_cases.export_tasks import ExportTasksUseCase
from core_logic.use_cases.compose_work_variants import ComposeWorkVariantsUseCase
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.render_remedial_sheet_batch_document import (
    RenderRemedialSheetBatchDocumentUseCase,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeUseCase,
)
from core_logic.use_cases.render_work_document import RenderWorkDocumentUseCase
from core_logic.use_cases.render_event_performance_report_document import (
    RenderEventPerformanceReportDocumentUseCase,
)
from core_logic.use_cases.render_student_digest_document import (
    RenderStudentDigestDocumentUseCase,
)
from core_logic.use_cases.create_presentation_profile import (
    CreatePresentationProfileUseCase,
)
from core_logic.use_cases.update_presentation_profile import (
    UpdatePresentationProfileUseCase,
)
from core_logic.use_cases.grade_student_work import GradeStudentWorkUseCase
from core_logic.use_cases.get_add_tasks_to_group import GetAddTasksToGroupUseCase
from core_logic.use_cases.get_academic_year_list import (
    GetAcademicYearListUseCase,
)
from core_logic.use_cases.get_codifier_detail import GetCodifierDetailUseCase
from core_logic.use_cases.get_codifier_list import GetCodifierListUseCase
from core_logic.use_cases.get_course_detail import GetCourseDetailUseCase
from core_logic.use_cases.get_course_list import GetCourseListUseCase
from core_logic.use_cases.get_dashboard_summary import GetDashboardSummaryUseCase
from core_logic.use_cases.get_presentation_profile import (
    GetPresentationProfileUseCase,
)
from core_logic.use_cases.get_presentation_profile_list import (
    GetPresentationProfileListUseCase,
)
from core_logic.use_cases.get_document_section_catalog import (
    GetDocumentSectionCatalogUseCase,
)
from core_logic.use_cases.get_presentation_profile_editor_data import (
    GetPresentationProfileEditorDataUseCase,
)
from core_logic.use_cases.get_presentation_profile_form_data import (
    GetPresentationProfileFormDataUseCase,
)
from core_logic.use_cases.get_document_type_catalog import (
    GetDocumentTypeCatalogUseCase,
)
from core_logic.use_cases.get_global_search import GetGlobalSearchUseCase
from core_logic.use_cases.get_heatmap_course_overview import (
    GetHeatmapCourseOverviewUseCase,
)
from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    GetHeatmapCourseTopicMatrixUseCase,
)
from core_logic.use_cases.get_heatmap_course_timeline import (
    GetHeatmapCourseTimelineUseCase,
)
from core_logic.use_cases.get_heatmap_drilldown_overview import (
    GetHeatmapDrilldownOverviewUseCase,
)
from core_logic.use_cases.get_heatmap_overview import GetHeatmapOverviewUseCase
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
from core_logic.use_cases.get_import_views import (
    GetImportHistoryUseCase,
    GetImportPageUseCase,
)
from core_logic.use_cases.get_journal import GetJournalUseCase
from core_logic.use_cases.get_journal_select import GetJournalSelectUseCase
from core_logic.use_cases.get_participation_review import (
    GetParticipationReviewUseCase,
)
from core_logic.use_cases.get_event_review import GetEventReviewUseCase
from core_logic.use_cases.get_event_detail import GetEventDetailUseCase
from core_logic.use_cases.get_event_list import GetEventListUseCase
from core_logic.use_cases.get_event_participant_selection import (
    GetEventParticipantSelectionUseCase,
)
from core_logic.use_cases.get_event_participation_ref import (
    GetEventParticipationRefUseCase,
)
from core_logic.use_cases.get_event_variant_assignment import (
    GetEventVariantAssignmentUseCase,
)
from core_logic.use_cases.get_events_status_report import (
    GetEventsStatusReportUseCase,
)
from core_logic.use_cases.get_event_performance_report import (
    GetEventPerformanceReportUseCase,
)
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileUseCase,
)
from core_logic.use_cases.get_orphan_variant_list import GetOrphanVariantListUseCase
from core_logic.use_cases.get_remedial_event_preview import (
    GetRemedialEventPreviewUseCase,
)
from core_logic.use_cases.get_remedial_sheet_data import (
    GetRemedialSheetDataUseCase,
)
from core_logic.use_cases.get_recent_review_sessions import (
    GetRecentReviewSessionsUseCase,
)
from core_logic.use_cases.get_remedial_wizard_preview import (
    GetRemedialWizardPreviewUseCase,
)
from core_logic.use_cases.get_remedial_wizard_start import (
    GetRemedialWizardStartUseCase,
)
from core_logic.use_cases.get_review_dashboard import GetReviewDashboardUseCase
from core_logic.use_cases.get_review_save_navigation import (
    GetReviewSaveNavigationUseCase,
)
from core_logic.use_cases.get_site_settings import GetSiteSettingsUseCase
from core_logic.use_cases.get_student_detail import GetStudentDetailUseCase
from core_logic.use_cases.get_student_group_detail import GetStudentGroupDetailUseCase
from core_logic.use_cases.get_student_group_list import GetStudentGroupListUseCase
from core_logic.use_cases.get_student_list import GetStudentListUseCase
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from core_logic.use_cases.get_student_remedial_work import (
    GetStudentRemedialWorkUseCase,
)
from core_logic.use_cases.get_task_detail import GetTaskDetailUseCase
from core_logic.use_cases.get_task_db_health import GetTaskDBHealthUseCase
from core_logic.use_cases.get_task_group_detail import GetTaskGroupDetailUseCase
from core_logic.use_cases.get_task_group_list import GetTaskGroupListUseCase
from core_logic.use_cases.get_task_list import GetTaskListUseCase
from core_logic.use_cases.get_task_reference_options import (
    GetCodifierElementsUseCase,
    GetSubtopicOptionsUseCase,
)
from core_logic.use_cases.get_topic_subtopics import GetTopicSubtopicsUseCase
from core_logic.use_cases.get_topic_detail import GetTopicDetailUseCase
from core_logic.use_cases.get_topic_list import GetTopicListUseCase
from core_logic.use_cases.get_variant_detail import GetVariantDetailUseCase
from core_logic.use_cases.get_variant_generation_form import (
    GetVariantGenerationFormUseCase,
)
from core_logic.use_cases.get_variant_list import GetVariantListUseCase
from core_logic.use_cases.get_work_detail import GetWorkDetailUseCase
from core_logic.use_cases.get_work_form_data import GetWorkFormDataUseCase
from core_logic.use_cases.get_work_list import GetWorkListUseCase
from core_logic.use_cases.get_work_analysis_report import (
    GetWorkAnalysisReportUseCase,
)
from core_logic.use_cases.get_reports_dashboard import GetReportsDashboardUseCase
from core_logic.use_cases.get_student_performance_report import (
    GetStudentPerformanceReportUseCase,
)
from core_logic.use_cases.get_student_digests import GetStudentDigestsUseCase
from core_logic.use_cases.get_variant_delete_info import GetVariantDeleteInfoUseCase
from core_logic.use_cases.prepare_participation_review_submission import (
    PrepareParticipationReviewSubmissionUseCase,
)
from core_logic.use_cases.prepare_event_action_submission import (
    PrepareAssignSingleVariantSubmissionUseCase,
    PrepareChangeEventStatusSubmissionUseCase,
)
from core_logic.use_cases.prepare_remedial_from_event_submission import (
    PrepareRemedialFromEventSubmissionUseCase,
)
from core_logic.use_cases.prepare_remedial_wizard_submission import (
    PrepareRemedialWizardCreateSubmissionUseCase,
    PrepareRemedialWizardPreviewSubmissionUseCase,
)
from core_logic.use_cases.prepare_student_remedial_submission import (
    PrepareStudentRemedialSubmissionUseCase,
)
from core_logic.use_cases.prepare_task_group_membership_submission import (
    PrepareAddTasksToGroupSubmissionUseCase,
    PrepareUpdateTaskGroupRolesSubmissionUseCase,
)
from core_logic.use_cases.prepare_work_variant_submission import (
    PrepareBulkDeleteVariantsSubmissionUseCase,
    PrepareCreateWorkFromOrphansSubmissionUseCase,
    PrepareDeleteVariantSubmissionUseCase,
)
from core_logic.use_cases.get_source_list import GetSourceListUseCase
from core_logic.use_cases.get_task_import_sample import GetTaskImportSampleUseCase
from core_logic.use_cases.preview_task_import import PreviewTaskImportUseCase
from core_logic.use_cases.preview_task_import_file import (
    PreviewTaskImportFileUseCase,
)
from core_logic.use_cases.prepare_task_import_file import (
    PrepareTaskImportExecutionSubmissionUseCase,
    PrepareTaskImportFileUseCase,
)
from core_logic.use_cases.refresh_task_math_cache import RefreshTaskMathCacheUseCase
from core_logic.use_cases.resolve_academic_year import ResolveAcademicYearUseCase
from core_logic.use_cases.save_analog_group import (
    CreateAnalogGroupUseCase,
    UpdateAnalogGroupUseCase,
)
from core_logic.use_cases.save_event import CreateEventUseCase, UpdateEventUseCase
from core_logic.use_cases.save_event_report_narrative import (
    SaveEventReportNarrativeUseCase,
)
from core_logic.use_cases.save_student import (
    CreateStudentGroupUseCase,
    CreateStudentUseCase,
    UpdateStudentGroupUseCase,
    UpdateStudentUseCase,
)
from core_logic.use_cases.save_site_settings import SaveSiteSettingsUseCase
from core_logic.use_cases.save_task import (
    CreateTaskUseCase,
    SaveTaskImagesUseCase,
    UpdateTaskUseCase,
)
from core_logic.use_cases.save_work import (
    CreateWorkWithSpecificationUseCase,
    UpdateWorkWithSpecificationUseCase,
)
from core_logic.use_cases.sync_review_session import SyncReviewSessionUseCase
from core_logic.use_cases.sync_work_analog_groups import SyncWorkAnalogGroupsUseCase
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentUseCase,
)
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonUseCase,
)
from core_logic.use_cases.validate_review_work_scan import (
    ValidateReviewWorkScanUseCase,
)
from infrastructure.repositories.django_academic_year_repo import (
    DjangoAcademicYearRepository,
)
from infrastructure.repositories.django_attempt_snapshot_repo import (
    DjangoAttemptSnapshotRepository,
)
from infrastructure.repositories.django_codifier_repo import DjangoCodifierRepository
from infrastructure.repositories.django_core_repo import DjangoCoreRepository
from infrastructure.repositories.django_curriculum_repo import (
    DjangoCurriculumRepository,
)
from infrastructure.repositories.django_presentation_profile_repo import (
    DjangoPresentationProfileRepository,
)
from infrastructure.repositories.django_event_repo import DjangoEventRepository
from infrastructure.repositories.django_participation_grading_repo import (
    DjangoParticipationGradingRepository,
)
from infrastructure.repositories.django_event_performance_report_repo import (
    DjangoEventPerformanceReportRepository,
)
from infrastructure.repositories.django_events_status_repo import (
    DjangoEventsStatusRepository,
)
from infrastructure.repositories.django_journal_repo import (
    DjangoJournalRepository,
)
from infrastructure.repositories.django_review_repo import DjangoReviewRepository
from infrastructure.repositories.django_review_session_repo import (
    DjangoReviewSessionRepository,
)
from infrastructure.repositories.django_review_task_repo import (
    DjangoReviewTaskRepository,
)
from infrastructure.repositories.django_heatmap_detail_repo import DjangoHeatmapDetailRepository
from infrastructure.repositories.django_heatmap_overview_repo import (
    DjangoHeatmapOverviewRepository,
)
from infrastructure.repositories.django_heatmap_matrix_repo import (
    DjangoHeatmapMatrixRepository,
)
from infrastructure.repositories.django_reports_dashboard_repo import (
    DjangoReportsDashboardRepository,
)
from infrastructure.repositories.django_settings_repo import DjangoSettingsRepository
from infrastructure.repositories.django_source_repo import DjangoSourceRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_student_digest_repo import (
    DjangoStudentDigestRepository,
)
from infrastructure.repositories.django_student_performance_repo import (
    DjangoStudentPerformanceRepository,
)
from infrastructure.repositories.django_task_repo import DjangoTaskRepository
from infrastructure.repositories.django_task_catalog_repo import (
    DjangoTaskCatalogRepository,
)
from infrastructure.repositories.django_task_export_repo import (
    DjangoTaskExportRepository,
)
from infrastructure.repositories.django_task_group_repo import (
    DjangoTaskGroupRepository,
)
from infrastructure.repositories.django_task_image_audit_repo import (
    DjangoTaskImageAuditRepository,
)
from infrastructure.repositories.django_task_db_health_repo import (
    DjangoTaskDBHealthRepository,
)
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from infrastructure.repositories.django_work_read_repo import (
    DjangoWorkReadRepository,
)
from infrastructure.repositories.django_variant_read_repo import (
    DjangoVariantReadRepository,
)
from infrastructure.repositories.django_work_document_repo import (
    DjangoWorkDocumentRepository,
)
from infrastructure.repositories.django_remedial_source_repo import (
    DjangoRemedialSourceRepository,
)
from infrastructure.repositories.django_work_analysis_repo import (
    DjangoWorkAnalysisRepository,
)
from infrastructure.services.document_engine import (
    DjangoDocumentEngine,
)
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_defaults import (
    build_sectioned_document_components,
)
from infrastructure.services.django_transaction_manager import (
    DjangoTransactionManager,
)
from infrastructure.services.task_import_service import DjangoTaskImportService
from infrastructure.services.task_math_status_cache import (
    task_math_status_cache,
)
from infrastructure.forms.codifier_forms import CodifierFormAdapter
from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.curriculum_forms import CurriculumFormAdapter
from infrastructure.forms.presentation_profile_forms import (
    PresentationProfileFormAdapter,
)
from infrastructure.forms.event_forms import EventFormAdapter
from infrastructure.forms.report_forms import ReportFormAdapter
from infrastructure.forms.review_forms import ReviewFormAdapter
from infrastructure.forms.settings_forms import SettingsFormAdapter
from infrastructure.forms.student_forms import StudentFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter
from infrastructure.forms.work_forms import WorkFormAdapter
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.presenters.heatmap import HeatmapPresenter
from infrastructure.presenters.rendered_document_file import (
    RenderedDocumentFilePresenter,
)
from infrastructure.presenters.report_document import (
    ReportDocumentWebPresenter,
)
from infrastructure.presenters.work_document import WorkDocumentWebPresenter


class Container:
    """Wires pure use cases to Django infrastructure adapters."""

    def __init__(self):
        self._academic_year_repo = None
        self._attempt_snapshot_repo = None
        self._student_repo = None
        self._student_learning_repo = None
        self._source_repo = None
        self._task_repo = None
        self._task_catalog_repo = None
        self._task_export_repo = None
        self._task_group_repo = None
        self._task_math_status_cache = None
        self._task_image_audit_repo = None
        self._work_repo = None
        self._work_read_repo = None
        self._variant_read_repo = None
        self._work_document_repo = None
        self._remedial_source_repo = None
        self._event_repo = None
        self._participation_grading_repo = None
        self._review_repo = None
        self._review_session_repo = None
        self._review_task_repo = None
        self._events_status_repo = None
        self._reports_dashboard_repo = None
        self._student_performance_repo = None
        self._work_analysis_repo = None
        self._heatmap_detail_repo = None
        self._heatmap_matrix_repo = None
        self._heatmap_overview_repo = None
        self._journal_repo = None
        self._task_db_health_repo = None
        self._event_performance_report_repo = None
        self._student_digest_repo = None
        self._curriculum_repo = None
        self._codifier_repo = None
        self._core_repo = None
        self._settings_repo = None
        self._presentation_profile_repo = None
        self._codifier_form_adapter = None
        self._core_form_adapter = None
        self._curriculum_form_adapter = None
        self._presentation_profile_form_adapter = None
        self._event_form_adapter = None
        self._report_form_adapter = None
        self._heatmap_presenter = None
        self._review_form_adapter = None
        self._settings_form_adapter = None
        self._student_form_adapter = None
        self._task_group_form_adapter = None
        self._work_form_adapter = None
        self._work_document_web_presenter = None
        self._rendered_document_file_presenter = None
        self._report_document_web_presenter = None
        self._task_form_adapter = None
        self._document_engine = None
        self._rendered_document_file_store = None
        self._task_import_service = None
        self._transaction_manager = None

    @property
    def academic_year_repo(self):
        if self._academic_year_repo is None:
            self._academic_year_repo = DjangoAcademicYearRepository()
        return self._academic_year_repo

    @property
    def attempt_snapshot_repo(self):
        if self._attempt_snapshot_repo is None:
            self._attempt_snapshot_repo = DjangoAttemptSnapshotRepository()
        return self._attempt_snapshot_repo

    @property
    def student_repo(self):
        if self._student_repo is None:
            self._student_repo = DjangoStudentRepository()
        return self._student_repo

    @property
    def student_learning_repo(self):
        if self._student_learning_repo is None:
            self._student_learning_repo = self.student_repo
        return self._student_learning_repo

    @property
    def source_repo(self):
        if self._source_repo is None:
            self._source_repo = DjangoSourceRepository()
        return self._source_repo

    @property
    def task_repo(self):
        if self._task_repo is None:
            self._task_repo = DjangoTaskRepository(
                math_status_cache=self.task_math_status_cache,
            )
        return self._task_repo

    @property
    def task_catalog_repo(self):
        if self._task_catalog_repo is None:
            self._task_catalog_repo = DjangoTaskCatalogRepository()
        return self._task_catalog_repo

    @property
    def task_export_repo(self):
        if self._task_export_repo is None:
            self._task_export_repo = DjangoTaskExportRepository()
        return self._task_export_repo

    @property
    def task_group_repo(self):
        if self._task_group_repo is None:
            self._task_group_repo = DjangoTaskGroupRepository()
        return self._task_group_repo

    @property
    def task_math_status_cache(self):
        if self._task_math_status_cache is None:
            self._task_math_status_cache = task_math_status_cache
        return self._task_math_status_cache

    @property
    def task_image_audit_repo(self):
        if self._task_image_audit_repo is None:
            self._task_image_audit_repo = DjangoTaskImageAuditRepository()
        return self._task_image_audit_repo

    @property
    def work_repo(self):
        if self._work_repo is None:
            self._work_repo = DjangoWorkRepository()
        return self._work_repo

    @property
    def work_read_repo(self):
        if self._work_read_repo is None:
            self._work_read_repo = DjangoWorkReadRepository()
        return self._work_read_repo

    @property
    def variant_read_repo(self):
        if self._variant_read_repo is None:
            self._variant_read_repo = DjangoVariantReadRepository()
        return self._variant_read_repo

    @property
    def work_document_repo(self):
        if self._work_document_repo is None:
            self._work_document_repo = DjangoWorkDocumentRepository()
        return self._work_document_repo

    @property
    def remedial_source_repo(self):
        if self._remedial_source_repo is None:
            self._remedial_source_repo = DjangoRemedialSourceRepository()
        return self._remedial_source_repo

    @property
    def event_repo(self):
        if self._event_repo is None:
            self._event_repo = DjangoEventRepository()
        return self._event_repo

    @property
    def participation_grading_repo(self):
        if self._participation_grading_repo is None:
            self._participation_grading_repo = (
                DjangoParticipationGradingRepository()
            )
        return self._participation_grading_repo

    @property
    def transaction_manager(self):
        if self._transaction_manager is None:
            self._transaction_manager = DjangoTransactionManager()
        return self._transaction_manager

    @property
    def review_repo(self):
        if self._review_repo is None:
            self._review_repo = DjangoReviewRepository()
        return self._review_repo

    @property
    def review_session_repo(self):
        if self._review_session_repo is None:
            self._review_session_repo = DjangoReviewSessionRepository()
        return self._review_session_repo

    @property
    def review_task_repo(self):
        if self._review_task_repo is None:
            self._review_task_repo = DjangoReviewTaskRepository()
        return self._review_task_repo

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
    def journal_repo(self):
        if self._journal_repo is None:
            self._journal_repo = DjangoJournalRepository()
        return self._journal_repo

    @property
    def task_db_health_repo(self):
        if self._task_db_health_repo is None:
            self._task_db_health_repo = DjangoTaskDBHealthRepository()
        return self._task_db_health_repo

    @property
    def event_performance_report_repo(self):
        if self._event_performance_report_repo is None:
            self._event_performance_report_repo = (
                DjangoEventPerformanceReportRepository()
            )
        return self._event_performance_report_repo

    @property
    def student_digest_repo(self):
        if self._student_digest_repo is None:
            self._student_digest_repo = DjangoStudentDigestRepository()
        return self._student_digest_repo

    @property
    def curriculum_repo(self):
        if self._curriculum_repo is None:
            self._curriculum_repo = DjangoCurriculumRepository()
        return self._curriculum_repo

    @property
    def codifier_repo(self):
        if self._codifier_repo is None:
            self._codifier_repo = DjangoCodifierRepository()
        return self._codifier_repo

    @property
    def core_repo(self):
        if self._core_repo is None:
            self._core_repo = DjangoCoreRepository()
        return self._core_repo

    @property
    def settings_repo(self):
        if self._settings_repo is None:
            self._settings_repo = DjangoSettingsRepository()
        return self._settings_repo

    @property
    def presentation_profile_repo(self):
        if self._presentation_profile_repo is None:
            self._presentation_profile_repo = DjangoPresentationProfileRepository()
        return self._presentation_profile_repo

    @property
    def core_form_adapter(self):
        if self._core_form_adapter is None:
            self._core_form_adapter = CoreFormAdapter()
        return self._core_form_adapter

    @property
    def codifier_form_adapter(self):
        if self._codifier_form_adapter is None:
            self._codifier_form_adapter = CodifierFormAdapter()
        return self._codifier_form_adapter

    @property
    def curriculum_form_adapter(self):
        if self._curriculum_form_adapter is None:
            self._curriculum_form_adapter = CurriculumFormAdapter()
        return self._curriculum_form_adapter

    @property
    def presentation_profile_form_adapter(self):
        if self._presentation_profile_form_adapter is None:
            self._presentation_profile_form_adapter = PresentationProfileFormAdapter()
        return self._presentation_profile_form_adapter

    @property
    def event_form_adapter(self):
        if self._event_form_adapter is None:
            self._event_form_adapter = EventFormAdapter()
        return self._event_form_adapter

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

    @property
    def review_form_adapter(self):
        if self._review_form_adapter is None:
            self._review_form_adapter = ReviewFormAdapter()
        return self._review_form_adapter

    @property
    def settings_form_adapter(self):
        if self._settings_form_adapter is None:
            self._settings_form_adapter = SettingsFormAdapter()
        return self._settings_form_adapter

    @property
    def student_form_adapter(self):
        if self._student_form_adapter is None:
            self._student_form_adapter = StudentFormAdapter()
        return self._student_form_adapter

    @property
    def task_group_form_adapter(self):
        if self._task_group_form_adapter is None:
            self._task_group_form_adapter = TaskGroupFormAdapter()
        return self._task_group_form_adapter

    @property
    def work_form_adapter(self):
        if self._work_form_adapter is None:
            self._work_form_adapter = WorkFormAdapter()
        return self._work_form_adapter

    @property
    def work_document_web_presenter(self):
        if self._work_document_web_presenter is None:
            self._work_document_web_presenter = WorkDocumentWebPresenter()
        return self._work_document_web_presenter

    @property
    def rendered_document_file_presenter(self):
        if self._rendered_document_file_presenter is None:
            self._rendered_document_file_presenter = (
                RenderedDocumentFilePresenter()
            )
        return self._rendered_document_file_presenter

    @property
    def report_document_web_presenter(self):
        if self._report_document_web_presenter is None:
            self._report_document_web_presenter = ReportDocumentWebPresenter()
        return self._report_document_web_presenter

    @property
    def task_form_adapter(self):
        if self._task_form_adapter is None:
            self._task_form_adapter = TaskFormAdapter()
        return self._task_form_adapter

    @property
    def document_engine(self):
        if self._document_engine is None:
            components = build_sectioned_document_components(
                work_document_repo=self.work_document_repo,
                get_remedial_sheet_data=(
                    self.get_remedial_sheet_data_use_case().execute
                ),
                get_event_report=(
                    self.get_event_performance_report_use_case().execute
                ),
                get_student_digests=(
                    self.get_student_digests_use_case().execute
                ),
                file_store=self.rendered_document_file_store,
            )
            self._document_engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=(
                    components.document_renderer_registry
                ),
            )
        return self._document_engine

    @property
    def rendered_document_file_store(self):
        if self._rendered_document_file_store is None:
            self._rendered_document_file_store = RenderedDocumentFileStore()
        return self._rendered_document_file_store

    @property
    def task_import_service(self):
        if self._task_import_service is None:
            self._task_import_service = DjangoTaskImportService()
        return self._task_import_service

    def remedial_service(self):
        return RemedialService(
            student_learning_repo=self.student_learning_repo,
            task_repo=self.task_repo,
            task_group_repo=self.task_group_repo,
            remedial_source_repo=self.remedial_source_repo,
        )

    def analytics_service(self):
        return StudentAnalyticsService()

    def grading_service(self):
        return GradingService()

    def event_service(self):
        return EventService()

    def review_service(self):
        return ReviewService()

    def work_service(self):
        return WorkService()

    def create_remedial_from_event_use_case(self):
        return CreateRemedialFromEventUseCase(
            remedial_service=self.remedial_service(),
            task_repo=self.task_repo,
            work_repo=self.work_repo,
            event_repo=self.event_repo,
            transaction_manager=self.transaction_manager,
        )

    def create_student_remedial_variant_use_case(self):
        return CreateStudentRemedialVariantUseCase(
            student_repo=self.student_repo,
            student_learning_repo=self.student_learning_repo,
            task_repo=self.task_repo,
            work_repo=self.work_repo,
        )

    def create_remedial_wizard_work_use_case(self):
        return CreateRemedialWizardWorkUseCase(
            student_repo=self.student_repo,
            task_repo=self.task_repo,
            work_repo=self.work_repo,
            event_repo=self.event_repo,
            transaction_manager=self.transaction_manager,
        )

    def get_remedial_event_preview_use_case(self):
        return GetRemedialEventPreviewUseCase(
            event_repo=self.event_repo,
        )

    def create_event_use_case(self):
        return CreateEventUseCase(
            event_repo=self.event_repo,
        )

    def update_event_use_case(self):
        return UpdateEventUseCase(
            event_repo=self.event_repo,
        )

    def get_remedial_wizard_preview_use_case(self):
        return GetRemedialWizardPreviewUseCase(
            student_learning_repo=self.student_learning_repo,
        )

    def get_remedial_wizard_start_use_case(self):
        return GetRemedialWizardStartUseCase(
            student_repo=self.student_repo,
        )

    def get_student_profile_use_case(self):
        return GetStudentProfileUseCase(
            student_repo=self.student_repo,
            student_learning_repo=self.student_learning_repo,
            analytics_service=self.analytics_service(),
        )

    def get_student_detail_use_case(self):
        return GetStudentDetailUseCase(
            student_repo=self.student_repo,
        )

    def get_student_group_detail_use_case(self):
        return GetStudentGroupDetailUseCase(
            student_repo=self.student_repo,
        )

    def get_student_list_use_case(self):
        return GetStudentListUseCase(
            student_repo=self.student_repo,
        )

    def resolve_academic_year_use_case(self):
        return ResolveAcademicYearUseCase(
            academic_year_repo=self.academic_year_repo,
        )

    def get_academic_year_list_use_case(self):
        return GetAcademicYearListUseCase(
            academic_year_repo=self.academic_year_repo,
        )

    def activate_academic_year_use_case(self):
        return ActivateAcademicYearUseCase(
            academic_year_repo=self.academic_year_repo,
        )

    def get_student_group_list_use_case(self):
        return GetStudentGroupListUseCase(
            student_repo=self.student_repo,
        )

    def get_student_remedial_work_use_case(self):
        return GetStudentRemedialWorkUseCase(
            student_learning_repo=self.student_learning_repo,
        )

    def create_student_use_case(self):
        return CreateStudentUseCase(
            student_repo=self.student_repo,
        )

    def update_student_use_case(self):
        return UpdateStudentUseCase(
            student_repo=self.student_repo,
        )

    def create_student_group_use_case(self):
        return CreateStudentGroupUseCase(
            student_repo=self.student_repo,
        )

    def update_student_group_use_case(self):
        return UpdateStudentGroupUseCase(
            student_repo=self.student_repo,
        )

    def get_task_list_use_case(self):
        return GetTaskListUseCase(
            task_repo=self.task_repo,
            task_catalog_repo=self.task_catalog_repo,
            task_group_repo=self.task_group_repo,
            math_status_cache=self.task_math_status_cache,
        )

    def get_task_group_list_use_case(self):
        return GetTaskGroupListUseCase(
            task_catalog_repo=self.task_catalog_repo,
            task_group_repo=self.task_group_repo,
        )

    def get_task_group_detail_use_case(self):
        return GetTaskGroupDetailUseCase(
            task_group_repo=self.task_group_repo,
        )

    def create_analog_group_use_case(self):
        return CreateAnalogGroupUseCase(
            task_group_repo=self.task_group_repo,
        )

    def update_analog_group_use_case(self):
        return UpdateAnalogGroupUseCase(
            task_group_repo=self.task_group_repo,
        )

    def get_add_tasks_to_group_use_case(self):
        return GetAddTasksToGroupUseCase(
            task_group_repo=self.task_group_repo,
        )

    def get_course_detail_use_case(self):
        return GetCourseDetailUseCase(
            curriculum_repo=self.curriculum_repo,
        )

    def get_course_list_use_case(self):
        return GetCourseListUseCase(
            curriculum_repo=self.curriculum_repo,
        )

    def get_topic_subtopics_use_case(self):
        return GetTopicSubtopicsUseCase(
            curriculum_repo=self.curriculum_repo,
        )

    def get_topic_list_use_case(self):
        return GetTopicListUseCase(
            curriculum_repo=self.curriculum_repo,
        )

    def get_topic_detail_use_case(self):
        return GetTopicDetailUseCase(
            curriculum_repo=self.curriculum_repo,
        )

    def get_codifier_list_use_case(self):
        return GetCodifierListUseCase(
            codifier_repo=self.codifier_repo,
        )

    def get_codifier_detail_use_case(self):
        return GetCodifierDetailUseCase(
            codifier_repo=self.codifier_repo,
        )

    def get_dashboard_summary_use_case(self):
        return GetDashboardSummaryUseCase(
            core_repo=self.core_repo,
        )

    def get_presentation_profile_list_use_case(self):
        return GetPresentationProfileListUseCase(
            presentation_profile_repo=self.presentation_profile_repo,
        )

    def get_presentation_profile_use_case(self):
        return GetPresentationProfileUseCase(
            presentation_profile_repo=self.presentation_profile_repo,
        )

    def create_presentation_profile_use_case(self):
        return CreatePresentationProfileUseCase(
            presentation_profile_repo=self.presentation_profile_repo,
        )

    def update_presentation_profile_use_case(self):
        return UpdatePresentationProfileUseCase(
            presentation_profile_repo=self.presentation_profile_repo,
        )

    def get_document_section_catalog_use_case(self):
        return GetDocumentSectionCatalogUseCase()

    def get_presentation_profile_editor_data_use_case(self):
        return GetPresentationProfileEditorDataUseCase(
            presentation_profile_repo=self.presentation_profile_repo,
        )

    def get_presentation_profile_form_data_use_case(self):
        return GetPresentationProfileFormDataUseCase(
            presentation_profile_repo=self.presentation_profile_repo,
        )

    def get_document_type_catalog_use_case(self):
        return GetDocumentTypeCatalogUseCase()

    def get_global_search_use_case(self):
        return GetGlobalSearchUseCase(
            core_repo=self.core_repo,
        )

    def get_import_page_use_case(self):
        return GetImportPageUseCase(
            core_repo=self.core_repo,
        )

    def get_import_history_use_case(self):
        return GetImportHistoryUseCase(
            core_repo=self.core_repo,
        )

    def get_site_settings_use_case(self):
        return GetSiteSettingsUseCase(
            settings_repo=self.settings_repo,
        )

    def save_site_settings_use_case(self):
        return SaveSiteSettingsUseCase(
            settings_repo=self.settings_repo,
        )

    def validate_task_import_json_use_case(self):
        return ValidateTaskImportJsonUseCase()

    def execute_task_import_use_case(self):
        return ExecuteTaskImportUseCase(
            task_import_service=self.task_import_service,
        )

    def execute_task_import_submission_use_case(self):
        return ExecuteTaskImportSubmissionUseCase(
            task_import_service=self.task_import_service,
        )

    def preview_task_import_use_case(self):
        return PreviewTaskImportUseCase(
            task_import_service=self.task_import_service,
        )

    def preview_task_import_file_use_case(self):
        return PreviewTaskImportFileUseCase(
            preview_task_import_use_case=self.preview_task_import_use_case(),
        )

    def prepare_task_import_file_use_case(self):
        return PrepareTaskImportFileUseCase()

    def prepare_task_import_execution_submission_use_case(self):
        return PrepareTaskImportExecutionSubmissionUseCase()

    def get_task_import_sample_use_case(self):
        return GetTaskImportSampleUseCase()

    def export_tasks_use_case(self):
        return ExportTasksUseCase(
            task_export_repo=self.task_export_repo,
        )

    def get_task_detail_use_case(self):
        return GetTaskDetailUseCase(
            task_repo=self.task_repo,
        )

    def get_subtopic_options_use_case(self):
        return GetSubtopicOptionsUseCase(
            task_catalog_repo=self.task_catalog_repo,
        )

    def get_codifier_elements_use_case(self):
        return GetCodifierElementsUseCase(
            task_catalog_repo=self.task_catalog_repo,
        )

    def get_source_list_use_case(self):
        return GetSourceListUseCase(
            source_repo=self.source_repo,
        )

    def create_source_use_case(self):
        return CreateSourceUseCase(
            source_repo=self.source_repo,
        )

    def refresh_task_math_cache_use_case(self):
        return RefreshTaskMathCacheUseCase(
            math_status_cache=self.task_math_status_cache,
        )

    def create_task_use_case(self):
        return CreateTaskUseCase(
            task_repo=self.task_repo,
            task_catalog_repo=self.task_catalog_repo,
        )

    def update_task_use_case(self):
        return UpdateTaskUseCase(
            task_repo=self.task_repo,
            task_catalog_repo=self.task_catalog_repo,
        )

    def save_task_images_use_case(self):
        return SaveTaskImagesUseCase(
            task_repo=self.task_repo,
        )

    def grade_student_work_use_case(self):
        return GradeStudentWorkUseCase(
            grading_repo=self.participation_grading_repo,
            review_task_repo=self.review_task_repo,
            grading_service=self.grading_service(),
            transaction_manager=self.transaction_manager,
            attempt_snapshot_repo=self.attempt_snapshot_repo,
        )

    def get_participation_review_use_case(self):
        return GetParticipationReviewUseCase(
            review_repo=self.review_repo,
            review_task_repo=self.review_task_repo,
            review_service=self.review_service(),
        )

    def get_review_dashboard_use_case(self):
        return GetReviewDashboardUseCase(
            review_repo=self.review_repo,
            review_service=self.review_service(),
        )

    def get_event_review_use_case(self):
        return GetEventReviewUseCase(
            event_repo=self.event_repo,
            review_repo=self.review_repo,
            review_service=self.review_service(),
        )

    def get_event_list_use_case(self):
        return GetEventListUseCase(
            event_repo=self.event_repo,
            event_service=self.event_service(),
        )

    def get_event_detail_use_case(self):
        return GetEventDetailUseCase(
            event_repo=self.event_repo,
            event_service=self.event_service(),
        )

    def get_event_participant_selection_use_case(self):
        return GetEventParticipantSelectionUseCase(
            event_repo=self.event_repo,
        )

    def get_event_participation_ref_use_case(self):
        return GetEventParticipationRefUseCase(
            event_repo=self.event_repo,
        )

    def get_event_variant_assignment_use_case(self):
        return GetEventVariantAssignmentUseCase(
            event_repo=self.event_repo,
        )

    def get_events_status_report_use_case(self):
        return GetEventsStatusReportUseCase(
            report_repo=self.events_status_repo,
        )

    def get_event_performance_report_use_case(self):
        return GetEventPerformanceReportUseCase(
            report_repo=self.event_performance_report_repo,
        )

    def save_event_report_narrative_use_case(self):
        return SaveEventReportNarrativeUseCase(
            report_repo=self.event_performance_report_repo,
        )

    def get_student_digests_use_case(self):
        return GetStudentDigestsUseCase(
            digest_repo=self.student_digest_repo,
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
            report_repo=self.journal_repo,
        )

    def get_journal_use_case(self):
        return GetJournalUseCase(
            report_repo=self.journal_repo,
        )

    def get_task_db_health_use_case(self):
        return GetTaskDBHealthUseCase(
            report_repo=self.task_db_health_repo,
        )

    def analyze_task_images_use_case(self):
        return AnalyzeTaskImagesUseCase(
            image_repo=self.task_image_audit_repo,
        )

    def apply_task_image_position_suggestions_use_case(self):
        return ApplyTaskImagePositionSuggestionsUseCase(
            image_repo=self.task_image_audit_repo,
        )

    def add_event_participants_use_case(self):
        return AddEventParticipantsUseCase(
            event_repo=self.event_repo,
        )

    def assign_event_variants_use_case(self):
        return AssignEventVariantsUseCase(
            event_repo=self.event_repo,
        )

    def assign_single_event_variant_use_case(self):
        return AssignSingleEventVariantUseCase(
            event_repo=self.event_repo,
        )

    def change_event_status_use_case(self):
        return ChangeEventStatusUseCase(
            event_repo=self.event_repo,
            event_service=self.event_service(),
        )

    def calculate_review_score_use_case(self):
        return CalculateReviewScoreUseCase(
            review_service=self.review_service(),
        )

    def finalize_review_event_use_case(self):
        return FinalizeReviewEventUseCase(
            review_repo=self.review_repo,
        )

    def toggle_participation_absent_use_case(self):
        return ToggleParticipationAbsentUseCase(
            review_repo=self.review_repo,
        )

    def prepare_participation_review_submission_use_case(self):
        return PrepareParticipationReviewSubmissionUseCase(
            review_service=self.review_service(),
        )

    def prepare_assign_single_variant_submission_use_case(self):
        return PrepareAssignSingleVariantSubmissionUseCase()

    def prepare_change_event_status_submission_use_case(self):
        return PrepareChangeEventStatusSubmissionUseCase()

    def prepare_remedial_from_event_submission_use_case(self):
        return PrepareRemedialFromEventSubmissionUseCase()

    def prepare_remedial_wizard_preview_submission_use_case(self):
        return PrepareRemedialWizardPreviewSubmissionUseCase()

    def prepare_remedial_wizard_create_submission_use_case(self):
        return PrepareRemedialWizardCreateSubmissionUseCase()

    def prepare_student_remedial_submission_use_case(self):
        return PrepareStudentRemedialSubmissionUseCase()

    def prepare_add_tasks_to_group_submission_use_case(self):
        return PrepareAddTasksToGroupSubmissionUseCase()

    def prepare_update_task_group_roles_submission_use_case(self):
        return PrepareUpdateTaskGroupRolesSubmissionUseCase()

    def prepare_delete_variant_submission_use_case(self):
        return PrepareDeleteVariantSubmissionUseCase()

    def prepare_bulk_delete_variants_submission_use_case(self):
        return PrepareBulkDeleteVariantsSubmissionUseCase()

    def prepare_create_work_from_orphans_submission_use_case(self):
        return PrepareCreateWorkFromOrphansSubmissionUseCase()

    def validate_review_work_scan_use_case(self):
        return ValidateReviewWorkScanUseCase(
            review_service=self.review_service(),
        )

    def get_review_save_navigation_use_case(self):
        return GetReviewSaveNavigationUseCase(
            review_repo=self.review_repo,
        )

    def get_recent_review_sessions_use_case(self):
        return GetRecentReviewSessionsUseCase(
            session_repo=self.review_session_repo,
        )

    def sync_review_session_use_case(self):
        return SyncReviewSessionUseCase(
            session_repo=self.review_session_repo,
        )

    def get_work_detail_use_case(self):
        return GetWorkDetailUseCase(
            work_read_repo=self.work_read_repo,
            work_service=self.work_service(),
            presentation_profile_repo=self.presentation_profile_repo,
        )

    def get_work_list_use_case(self):
        return GetWorkListUseCase(
            work_read_repo=self.work_read_repo,
        )

    def get_work_form_data_use_case(self):
        return GetWorkFormDataUseCase(
            work_read_repo=self.work_read_repo,
        )

    def get_variant_detail_use_case(self):
        return GetVariantDetailUseCase(
            variant_repo=self.variant_read_repo,
        )

    def get_variant_generation_form_use_case(self):
        return GetVariantGenerationFormUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_list_use_case(self):
        return GetVariantListUseCase(
            variant_repo=self.variant_read_repo,
        )

    def get_orphan_variant_list_use_case(self):
        return GetOrphanVariantListUseCase(
            orphan_variant_repo=self.work_repo,
        )

    def get_remedial_sheet_data_use_case(self):
        return GetRemedialSheetDataUseCase(
            work_repo=self.work_document_repo,
        )

    def sync_work_analog_groups_use_case(self):
        return SyncWorkAnalogGroupsUseCase(
            work_repo=self.work_repo,
            transaction_manager=self.transaction_manager,
        )

    def compose_work_variants_use_case(self):
        return ComposeWorkVariantsUseCase(
            work_repo=self.work_repo,
            transaction_manager=self.transaction_manager,
        )

    def render_work_document_use_case(self):
        return RenderWorkDocumentUseCase(
            work_repo=self.work_document_repo,
            presentation_profile_repo=self.presentation_profile_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def render_document_from_recipe_use_case(self):
        return RenderDocumentFromRecipeUseCase(
            document_engine=self.document_engine,
        )

    def render_remedial_sheet_document_use_case(self):
        return RenderRemedialSheetDocumentUseCase(
            work_repo=self.work_document_repo,
            presentation_profile_repo=self.presentation_profile_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def render_event_performance_report_document_use_case(self):
        return RenderEventPerformanceReportDocumentUseCase(
            get_event_report_use_case=(
                self.get_event_performance_report_use_case()
            ),
            presentation_profile_repo=self.presentation_profile_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def render_student_digest_document_use_case(self):
        return RenderStudentDigestDocumentUseCase(
            get_student_digests_use_case=self.get_student_digests_use_case(),
            presentation_profile_repo=self.presentation_profile_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def render_remedial_sheet_batch_document_use_case(self):
        return RenderRemedialSheetBatchDocumentUseCase(
            work_repo=self.work_document_repo,
            presentation_profile_repo=self.presentation_profile_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def get_rendered_document_file_use_case(self):
        return GetRenderedDocumentFileUseCase(
            file_store=self.rendered_document_file_store,
        )

    def create_work_from_orphans_use_case(self):
        return CreateWorkFromOrphansUseCase(
            orphan_variant_repo=self.work_repo,
        )

    def create_work_from_groups_use_case(self):
        return CreateWorkFromGroupsUseCase(
            task_group_repo=self.task_group_repo,
            create_work_with_specification_use_case=(
                self.create_work_with_specification_use_case()
            ),
            compose_work_variants_use_case=(
                self.compose_work_variants_use_case()
            ),
        )

    def prepare_create_work_from_groups_submission_use_case(self):
        return PrepareCreateWorkFromGroupsSubmissionUseCase()

    def create_work_from_tasks_use_case(self):
        return CreateWorkFromTasksUseCase(
            task_repo=self.task_repo,
            work_repo=self.work_repo,
        )

    def create_work_with_specification_use_case(self):
        return CreateWorkWithSpecificationUseCase(
            work_repo=self.work_repo,
        )

    def update_work_with_specification_use_case(self):
        return UpdateWorkWithSpecificationUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_delete_info_use_case(self):
        return GetVariantDeleteInfoUseCase(
            variant_repo=self.work_repo,
        )

    def delete_variant_use_case(self):
        return DeleteVariantUseCase(
            variant_repo=self.work_repo,
        )

    def delete_task_groups_use_case(self):
        return DeleteTaskGroupsUseCase(
            task_group_repo=self.task_group_repo,
        )

    def delete_task_use_case(self):
        return DeleteTaskUseCase(
            task_repo=self.task_repo,
        )

    def add_tasks_to_group_use_case(self):
        return AddTasksToGroupUseCase(
            task_group_repo=self.task_group_repo,
        )

    def remove_task_from_group_use_case(self):
        return RemoveTaskFromGroupUseCase(
            task_group_repo=self.task_group_repo,
        )

    def update_task_group_roles_use_case(self):
        return UpdateTaskGroupRolesUseCase(
            task_group_repo=self.task_group_repo,
        )

    def bulk_create_group_from_tasks_use_case(self):
        return BulkCreateGroupFromTasksUseCase(
            task_repo=self.task_repo,
            task_group_repo=self.task_group_repo,
        )

    def bulk_add_tasks_to_group_use_case(self):
        return BulkAddTasksToGroupUseCase(
            task_repo=self.task_repo,
            task_group_repo=self.task_group_repo,
        )

    def bulk_remove_tasks_from_groups_use_case(self):
        return BulkRemoveTasksFromGroupsUseCase(
            task_group_repo=self.task_group_repo,
        )

    def bulk_delete_variants_use_case(self):
        return BulkDeleteVariantsUseCase(
            variant_repo=self.work_repo,
        )


container = Container()
