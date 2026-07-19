"""Small dependency container for application use cases."""

from core_logic.services.analytics_service import StudentAnalyticsService
from core_logic.services.event_service import EventService
from core_logic.services.grading_service import GradingService
from core_logic.services.remedial_service import RemedialService
from core_logic.services.review_service import ReviewService
from core_logic.services.work_service import WorkService
from core_logic.use_cases.add_event_participants import AddEventParticipantsUseCase
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
    CreateWorkFromGroupsUseCase,
)
from core_logic.use_cases.create_work_from_tasks import CreateWorkFromTasksUseCase
from core_logic.use_cases.delete_variant import DeleteVariantUseCase
from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsUseCase
from core_logic.use_cases.delete_task import DeleteTaskUseCase
from core_logic.use_cases.finalize_review_event import FinalizeReviewEventUseCase
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase
from core_logic.use_cases.export_tasks import ExportTasksUseCase
from core_logic.use_cases.compose_work_variants import ComposeWorkVariantsUseCase
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.render_work_document import RenderWorkDocumentUseCase
from core_logic.use_cases.grade_student_work import GradeStudentWorkUseCase
from core_logic.use_cases.get_add_tasks_to_group import GetAddTasksToGroupUseCase
from core_logic.use_cases.get_codifier_detail import GetCodifierDetailUseCase
from core_logic.use_cases.get_codifier_list import GetCodifierListUseCase
from core_logic.use_cases.get_course_detail import GetCourseDetailUseCase
from core_logic.use_cases.get_course_list import GetCourseListUseCase
from core_logic.use_cases.get_dashboard_summary import GetDashboardSummaryUseCase
from core_logic.use_cases.get_default_document_template import (
    GetDefaultDocumentTemplateUseCase,
)
from core_logic.use_cases.get_document_template_list import (
    GetDocumentTemplateListUseCase,
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
from core_logic.use_cases.get_generated_document_file import (
    GetGeneratedDocumentFileUseCase,
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
from core_logic.use_cases.get_variant_generation_placeholder import (
    GetVariantGenerationPlaceholderUseCase,
)
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
)
from core_logic.use_cases.prepare_work_variant_submission import (
    PrepareBulkDeleteVariantsSubmissionUseCase,
    PrepareCreateWorkFromOrphansSubmissionUseCase,
    PrepareDeleteVariantSubmissionUseCase,
)
from core_logic.use_cases.get_source_list import GetSourceListUseCase
from core_logic.use_cases.get_task_import_sample import GetTaskImportSampleUseCase
from core_logic.use_cases.preview_task_import import PreviewTaskImportUseCase
from core_logic.use_cases.prepare_task_import_file import (
    PrepareTaskImportExecutionSubmissionUseCase,
    PrepareTaskImportFileUseCase,
)
from core_logic.use_cases.refresh_task_math_cache import RefreshTaskMathCacheUseCase
from core_logic.use_cases.save_analog_group import (
    CreateAnalogGroupUseCase,
    UpdateAnalogGroupUseCase,
)
from core_logic.use_cases.save_event import CreateEventUseCase, UpdateEventUseCase
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
    CreateWorkUseCase,
    SaveWorkSpecificationUseCase,
    UpdateWorkUseCase,
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
from infrastructure.repositories.django_codifier_repo import DjangoCodifierRepository
from infrastructure.repositories.django_core_repo import DjangoCoreRepository
from infrastructure.repositories.django_curriculum_repo import (
    DjangoCurriculumRepository,
)
from infrastructure.repositories.django_document_template_repo import (
    DjangoDocumentTemplateRepository,
)
from infrastructure.repositories.django_event_repo import DjangoEventRepository
from infrastructure.repositories.django_review_repo import DjangoReviewRepository
from infrastructure.repositories.django_report_repo import DjangoReportRepository
from infrastructure.repositories.django_settings_repo import DjangoSettingsRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_task_repo import DjangoTaskRepository
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from infrastructure.services.document_rendering_service import (
    DjangoDocumentRenderingService,
)
from infrastructure.services.task_import_service import DjangoTaskImportService
from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.event_forms import EventFormAdapter
from infrastructure.forms.report_forms import ReportFormAdapter
from infrastructure.forms.settings_forms import SettingsFormAdapter
from infrastructure.forms.student_forms import StudentFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter
from infrastructure.forms.work_forms import WorkFormAdapter
from infrastructure.forms.task_forms import TaskFormAdapter


class Container:
    """Wires pure use cases to Django infrastructure adapters."""

    def __init__(self):
        self._student_repo = None
        self._task_repo = None
        self._work_repo = None
        self._event_repo = None
        self._review_repo = None
        self._report_repo = None
        self._curriculum_repo = None
        self._codifier_repo = None
        self._core_repo = None
        self._settings_repo = None
        self._document_template_repo = None
        self._core_form_adapter = None
        self._event_form_adapter = None
        self._report_form_adapter = None
        self._settings_form_adapter = None
        self._student_form_adapter = None
        self._task_group_form_adapter = None
        self._work_form_adapter = None
        self._task_form_adapter = None
        self._document_rendering_service = None
        self._task_import_service = None

    @property
    def student_repo(self):
        if self._student_repo is None:
            self._student_repo = DjangoStudentRepository()
        return self._student_repo

    @property
    def task_repo(self):
        if self._task_repo is None:
            self._task_repo = DjangoTaskRepository()
        return self._task_repo

    @property
    def work_repo(self):
        if self._work_repo is None:
            self._work_repo = DjangoWorkRepository()
        return self._work_repo

    @property
    def event_repo(self):
        if self._event_repo is None:
            self._event_repo = DjangoEventRepository()
        return self._event_repo

    @property
    def review_repo(self):
        if self._review_repo is None:
            self._review_repo = DjangoReviewRepository()
        return self._review_repo

    @property
    def report_repo(self):
        if self._report_repo is None:
            self._report_repo = DjangoReportRepository()
        return self._report_repo

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
    def document_template_repo(self):
        if self._document_template_repo is None:
            self._document_template_repo = DjangoDocumentTemplateRepository()
        return self._document_template_repo

    @property
    def core_form_adapter(self):
        if self._core_form_adapter is None:
            self._core_form_adapter = CoreFormAdapter()
        return self._core_form_adapter

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
    def task_form_adapter(self):
        if self._task_form_adapter is None:
            self._task_form_adapter = TaskFormAdapter()
        return self._task_form_adapter

    @property
    def document_rendering_service(self):
        if self._document_rendering_service is None:
            self._document_rendering_service = DjangoDocumentRenderingService(
                get_remedial_sheet_data_use_case=(
                    self.get_remedial_sheet_data_use_case()
                ),
            )
        return self._document_rendering_service

    @property
    def document_generation_service(self):
        return self.document_rendering_service

    @property
    def task_import_service(self):
        if self._task_import_service is None:
            self._task_import_service = DjangoTaskImportService()
        return self._task_import_service

    def remedial_service(self):
        return RemedialService(
            student_repo=self.student_repo,
            task_repo=self.task_repo,
            work_repo=self.work_repo,
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
        )

    def create_student_remedial_variant_use_case(self):
        return CreateStudentRemedialVariantUseCase(
            student_repo=self.student_repo,
            task_repo=self.task_repo,
            work_repo=self.work_repo,
        )

    def create_remedial_wizard_work_use_case(self):
        return CreateRemedialWizardWorkUseCase(
            student_repo=self.student_repo,
            task_repo=self.task_repo,
            work_repo=self.work_repo,
            event_repo=self.event_repo,
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
            student_repo=self.student_repo,
        )

    def get_remedial_wizard_start_use_case(self):
        return GetRemedialWizardStartUseCase(
            student_repo=self.student_repo,
        )

    def get_student_profile_use_case(self):
        return GetStudentProfileUseCase(
            student_repo=self.student_repo,
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

    def get_student_group_list_use_case(self):
        return GetStudentGroupListUseCase(
            student_repo=self.student_repo,
        )

    def get_student_remedial_work_use_case(self):
        return GetStudentRemedialWorkUseCase(
            student_repo=self.student_repo,
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
        )

    def get_task_group_list_use_case(self):
        return GetTaskGroupListUseCase(
            task_repo=self.task_repo,
        )

    def get_task_group_detail_use_case(self):
        return GetTaskGroupDetailUseCase(
            task_repo=self.task_repo,
        )

    def create_analog_group_use_case(self):
        return CreateAnalogGroupUseCase(
            task_repo=self.task_repo,
        )

    def update_analog_group_use_case(self):
        return UpdateAnalogGroupUseCase(
            task_repo=self.task_repo,
        )

    def get_add_tasks_to_group_use_case(self):
        return GetAddTasksToGroupUseCase(
            task_repo=self.task_repo,
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

    def get_document_template_list_use_case(self):
        return GetDocumentTemplateListUseCase(
            document_template_repo=self.document_template_repo,
        )

    def get_default_document_template_use_case(self):
        return GetDefaultDocumentTemplateUseCase(
            document_template_repo=self.document_template_repo,
        )

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

    def preview_task_import_use_case(self):
        return PreviewTaskImportUseCase(
            task_import_service=self.task_import_service,
        )

    def prepare_task_import_file_use_case(self):
        return PrepareTaskImportFileUseCase()

    def prepare_task_import_execution_submission_use_case(self):
        return PrepareTaskImportExecutionSubmissionUseCase()

    def get_task_import_sample_use_case(self):
        return GetTaskImportSampleUseCase()

    def export_tasks_use_case(self):
        return ExportTasksUseCase(
            task_repo=self.task_repo,
        )

    def get_task_detail_use_case(self):
        return GetTaskDetailUseCase(
            task_repo=self.task_repo,
        )

    def get_subtopic_options_use_case(self):
        return GetSubtopicOptionsUseCase(
            task_repo=self.task_repo,
        )

    def get_codifier_elements_use_case(self):
        return GetCodifierElementsUseCase(
            task_repo=self.task_repo,
        )

    def get_source_list_use_case(self):
        return GetSourceListUseCase(
            task_repo=self.task_repo,
        )

    def create_source_use_case(self):
        return CreateSourceUseCase(
            task_repo=self.task_repo,
        )

    def refresh_task_math_cache_use_case(self):
        return RefreshTaskMathCacheUseCase(
            task_repo=self.task_repo,
        )

    def create_task_use_case(self):
        return CreateTaskUseCase(
            task_repo=self.task_repo,
        )

    def update_task_use_case(self):
        return UpdateTaskUseCase(
            task_repo=self.task_repo,
        )

    def save_task_images_use_case(self):
        return SaveTaskImagesUseCase(
            task_repo=self.task_repo,
        )

    def grade_student_work_use_case(self):
        return GradeStudentWorkUseCase(
            event_repo=self.event_repo,
            grading_service=self.grading_service(),
        )

    def get_participation_review_use_case(self):
        return GetParticipationReviewUseCase(
            review_repo=self.review_repo,
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
            report_repo=self.report_repo,
        )

    def get_reports_dashboard_use_case(self):
        return GetReportsDashboardUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_overview_use_case(self):
        return GetHeatmapOverviewUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_course_overview_use_case(self):
        return GetHeatmapCourseOverviewUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_course_topic_matrix_use_case(self):
        return GetHeatmapCourseTopicMatrixUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_course_timeline_use_case(self):
        return GetHeatmapCourseTimelineUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_drilldown_overview_use_case(self):
        return GetHeatmapDrilldownOverviewUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_student_detail_use_case(self):
        return GetHeatmapStudentDetailUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_subtopic_detail_use_case(self):
        return GetHeatmapSubtopicDetailUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_subtopic_matrix_use_case(self):
        return GetHeatmapSubtopicMatrixUseCase(
            report_repo=self.report_repo,
        )

    def get_heatmap_topic_matrix_use_case(self):
        return GetHeatmapTopicMatrixUseCase(
            report_repo=self.report_repo,
        )

    def get_work_analysis_report_use_case(self):
        return GetWorkAnalysisReportUseCase(
            report_repo=self.report_repo,
        )

    def get_student_performance_report_use_case(self):
        return GetStudentPerformanceReportUseCase(
            report_repo=self.report_repo,
        )

    def get_journal_select_use_case(self):
        return GetJournalSelectUseCase(
            report_repo=self.report_repo,
        )

    def get_journal_use_case(self):
        return GetJournalUseCase(
            report_repo=self.report_repo,
        )

    def get_task_db_health_use_case(self):
        return GetTaskDBHealthUseCase(
            report_repo=self.report_repo,
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
            review_repo=self.review_repo,
        )

    def sync_review_session_use_case(self):
        return SyncReviewSessionUseCase(
            review_repo=self.review_repo,
        )

    def get_work_detail_use_case(self):
        return GetWorkDetailUseCase(
            work_repo=self.work_repo,
            work_service=self.work_service(),
        )

    def get_work_list_use_case(self):
        return GetWorkListUseCase(
            work_repo=self.work_repo,
        )

    def get_work_form_data_use_case(self):
        return GetWorkFormDataUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_detail_use_case(self):
        return GetVariantDetailUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_generation_placeholder_use_case(self):
        return GetVariantGenerationPlaceholderUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_generation_form_use_case(self):
        return GetVariantGenerationFormUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_list_use_case(self):
        return GetVariantListUseCase(
            work_repo=self.work_repo,
        )

    def get_orphan_variant_list_use_case(self):
        return GetOrphanVariantListUseCase(
            work_repo=self.work_repo,
        )

    def get_remedial_sheet_data_use_case(self):
        return GetRemedialSheetDataUseCase(
            work_repo=self.work_repo,
        )

    def sync_work_analog_groups_use_case(self):
        return SyncWorkAnalogGroupsUseCase(
            work_repo=self.work_repo,
        )

    def compose_work_variants_use_case(self):
        return ComposeWorkVariantsUseCase(
            work_repo=self.work_repo,
        )

    def generate_work_variants_use_case(self):
        return self.compose_work_variants_use_case()

    def render_work_document_use_case(self):
        return RenderWorkDocumentUseCase(
            document_rendering_service=self.document_rendering_service,
            work_repo=self.work_repo,
            document_template_repo=self.document_template_repo,
        )

    def generate_work_document_use_case(self):
        return self.render_work_document_use_case()

    def render_remedial_sheet_document_use_case(self):
        return RenderRemedialSheetDocumentUseCase(
            document_rendering_service=self.document_rendering_service,
            work_repo=self.work_repo,
            document_template_repo=self.document_template_repo,
        )

    def generate_remedial_sheet_document_use_case(self):
        return self.render_remedial_sheet_document_use_case()

    def get_generated_document_file_use_case(self):
        return GetGeneratedDocumentFileUseCase(
            document_rendering_service=self.document_rendering_service,
        )

    def create_work_from_orphans_use_case(self):
        return CreateWorkFromOrphansUseCase(
            work_repo=self.work_repo,
        )

    def create_work_from_groups_use_case(self):
        return CreateWorkFromGroupsUseCase(
            task_repo=self.task_repo,
            work_repo=self.work_repo,
        )

    def create_work_from_tasks_use_case(self):
        return CreateWorkFromTasksUseCase(
            task_repo=self.task_repo,
            work_repo=self.work_repo,
        )

    def create_work_use_case(self):
        return CreateWorkUseCase(
            work_repo=self.work_repo,
        )

    def update_work_use_case(self):
        return UpdateWorkUseCase(
            work_repo=self.work_repo,
        )

    def save_work_specification_use_case(self):
        return SaveWorkSpecificationUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_delete_info_use_case(self):
        return GetVariantDeleteInfoUseCase(
            work_repo=self.work_repo,
        )

    def delete_variant_use_case(self):
        return DeleteVariantUseCase(
            work_repo=self.work_repo,
        )

    def delete_task_groups_use_case(self):
        return DeleteTaskGroupsUseCase(
            task_repo=self.task_repo,
        )

    def delete_task_use_case(self):
        return DeleteTaskUseCase(
            task_repo=self.task_repo,
        )

    def add_tasks_to_group_use_case(self):
        return AddTasksToGroupUseCase(
            task_repo=self.task_repo,
        )

    def remove_task_from_group_use_case(self):
        return RemoveTaskFromGroupUseCase(
            task_repo=self.task_repo,
        )

    def bulk_create_group_from_tasks_use_case(self):
        return BulkCreateGroupFromTasksUseCase(
            task_repo=self.task_repo,
        )

    def bulk_add_tasks_to_group_use_case(self):
        return BulkAddTasksToGroupUseCase(
            task_repo=self.task_repo,
        )

    def bulk_remove_tasks_from_groups_use_case(self):
        return BulkRemoveTasksFromGroupsUseCase(
            task_repo=self.task_repo,
        )

    def bulk_delete_variants_use_case(self):
        return BulkDeleteVariantsUseCase(
            work_repo=self.work_repo,
        )


container = Container()
