"""Small dependency container for application use cases."""

from core_logic.services.analytics_service import StudentAnalyticsService
from core_logic.use_cases.analyze_task_images import (
    AnalyzeTaskImagesUseCase,
    ApplyTaskImagePositionSuggestionsUseCase,
)
from core_logic.use_cases.activate_academic_year import (
    ActivateAcademicYearUseCase,
)
from core_logic.use_cases.backfill_task_classifications import (
    BackfillTaskClassificationsUseCase,
)
from core_logic.use_cases.bulk_change_task_groups import (
    BulkAddTasksToGroupUseCase,
    BulkCreateGroupFromTasksUseCase,
    BulkRemoveTasksFromGroupsUseCase,
)
from core_logic.use_cases.change_task_group_membership import (
    AddTasksToGroupUseCase,
    RemoveTaskFromGroupUseCase,
    UpdateTaskGroupRolesUseCase,
)
from core_logic.use_cases.create_source import CreateSourceUseCase
from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsUseCase
from core_logic.use_cases.delete_task import DeleteTaskUseCase
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase
from core_logic.use_cases.execute_task_import_submission import (
    ExecuteTaskImportSubmissionUseCase,
)
from core_logic.use_cases.export_tasks import ExportTasksUseCase
from core_logic.use_cases.import_students import ImportStudentsUseCase
from core_logic.use_cases.import_codifier import ImportCodifierUseCase
from core_logic.use_cases.import_curriculum import ImportCurriculumUseCase
from core_logic.use_cases.get_add_tasks_to_group import GetAddTasksToGroupUseCase
from core_logic.use_cases.get_academic_year_list import (
    GetAcademicYearListUseCase,
)
from core_logic.use_cases.get_codifier_detail import GetCodifierDetailUseCase
from core_logic.use_cases.get_codifier_list import GetCodifierListUseCase
from core_logic.use_cases.get_course_detail import GetCourseDetailUseCase
from core_logic.use_cases.get_course_list import GetCourseListUseCase
from core_logic.use_cases.get_dashboard_summary import GetDashboardSummaryUseCase
from core_logic.use_cases.get_global_search import GetGlobalSearchUseCase
from core_logic.use_cases.get_import_views import (
    GetImportHistoryUseCase,
    GetImportPageUseCase,
)
from core_logic.use_cases.get_site_settings import GetSiteSettingsUseCase
from core_logic.use_cases.get_student_detail import GetStudentDetailUseCase
from core_logic.use_cases.get_student_group_detail import GetStudentGroupDetailUseCase
from core_logic.use_cases.get_student_group_list import GetStudentGroupListUseCase
from core_logic.use_cases.get_student_list import GetStudentListUseCase
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from core_logic.use_cases.get_task_detail import GetTaskDetailUseCase
from core_logic.use_cases.get_task_db_health import GetTaskDBHealthUseCase
from core_logic.use_cases.get_task_group_detail import GetTaskGroupDetailUseCase
from core_logic.use_cases.get_task_group_list import GetTaskGroupListUseCase
from core_logic.use_cases.get_task_list import GetTaskListUseCase
from core_logic.use_cases.get_task_classification_options import (
    GetTaskClassificationOptionsUseCase,
)
from core_logic.use_cases.get_task_reference_options import (
    GetSubtopicOptionsUseCase,
)
from core_logic.use_cases.get_topic_subtopics import GetTopicSubtopicsUseCase
from core_logic.use_cases.get_topic_detail import GetTopicDetailUseCase
from core_logic.use_cases.get_topic_list import GetTopicListUseCase
from core_logic.use_cases.prepare_task_group_membership_submission import (
    PrepareAddTasksToGroupSubmissionUseCase,
    PrepareUpdateTaskGroupRolesSubmissionUseCase,
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
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonUseCase,
)
from infrastructure.repositories.django_academic_year_activation_repo import (
    DjangoAcademicYearActivationRepository,
)
from infrastructure.repositories.django_academic_year_catalog_repo import (
    DjangoAcademicYearCatalogRepository,
)
from infrastructure.repositories.django_codifier_catalog_repo import (
    DjangoCodifierCatalogRepository,
)
from infrastructure.repositories.django_codifier_detail_repo import (
    DjangoCodifierDetailRepository,
)
from infrastructure.repositories.django_codifier_import_repo import (
    DjangoCodifierImportRepository,
)
from infrastructure.repositories.django_dashboard_summary_repo import (
    DjangoDashboardSummaryRepository,
)
from infrastructure.repositories.django_global_search_repo import (
    DjangoGlobalSearchRepository,
)
from infrastructure.repositories.django_import_log_repo import (
    DjangoImportLogRepository,
)
from infrastructure.repositories.django_course_catalog_repo import (
    DjangoCourseCatalogRepository,
)
from infrastructure.repositories.django_curriculum_import_repo import (
    DjangoCurriculumImportRepository,
)
from infrastructure.repositories.django_topic_catalog_repo import (
    DjangoTopicCatalogRepository,
)
from infrastructure.repositories.django_site_settings_command_repo import (
    DjangoSiteSettingsCommandRepository,
)
from infrastructure.repositories.django_site_settings_query_repo import (
    DjangoSiteSettingsQueryRepository,
)
from infrastructure.repositories.django_source_catalog_repo import (
    DjangoSourceCatalogRepository,
)
from infrastructure.repositories.django_source_command_repo import (
    DjangoSourceCommandRepository,
)
from infrastructure.repositories.django_student_catalog_repo import (
    DjangoStudentCatalogRepository,
)
from infrastructure.repositories.django_student_command_repo import (
    DjangoStudentCommandRepository,
)
from infrastructure.repositories.django_student_group_catalog_repo import (
    DjangoStudentGroupCatalogRepository,
)
from infrastructure.repositories.django_student_group_command_repo import (
    DjangoStudentGroupCommandRepository,
)
from infrastructure.repositories.django_student_import_command_repo import (
    DjangoStudentImportCommandRepository,
)
from infrastructure.repositories.django_student_import_snapshot_repo import (
    DjangoStudentImportSnapshotRepository,
)
from infrastructure.repositories.django_student_profile_repo import (
    DjangoStudentProfileRepository,
)
from infrastructure.repositories.django_task_read_repo import (
    DjangoTaskReadRepository,
)
from infrastructure.repositories.django_task_command_repo import (
    DjangoTaskCommandRepository,
)
from infrastructure.repositories.django_task_classification_repo import (
    DjangoTaskClassificationRepository,
)
from infrastructure.repositories.django_task_classification_backfill_repo import (
    DjangoTaskClassificationBackfillRepository,
)
from infrastructure.repositories.django_task_image_command_repo import (
    DjangoTaskImageCommandRepository,
)
from infrastructure.repositories.django_task_lifecycle_command_repo import (
    DjangoTaskLifecycleCommandRepository,
)
from infrastructure.repositories.django_task_selection_repo import (
    DjangoTaskSelectionRepository,
)
from infrastructure.repositories.django_task_taxonomy_repo import (
    DjangoTaskTaxonomyRepository,
)
from infrastructure.repositories.django_task_export_repo import (
    DjangoTaskExportRepository,
)
from infrastructure.repositories.django_task_group_catalog_repo import (
    DjangoTaskGroupCatalogRepository,
)
from infrastructure.repositories.django_task_group_management_repo import (
    DjangoTaskGroupManagementRepository,
)
from infrastructure.repositories.django_task_image_audit_command_repo import (
    DjangoTaskImageAuditCommandRepository,
)
from infrastructure.repositories.django_task_image_audit_query_repo import (
    DjangoTaskImageAuditQueryRepository,
)
from infrastructure.repositories.django_task_db_health_repo import (
    DjangoTaskDBHealthRepository,
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
from infrastructure.forms.settings_forms import SettingsFormAdapter
from infrastructure.forms.student_forms import StudentFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.containers.document import DocumentCompositionMixin
from infrastructure.containers.event import EventCompositionMixin
from infrastructure.containers.remedial import RemedialCompositionMixin
from infrastructure.containers.reporting import ReportingCompositionMixin
from infrastructure.containers.review import ReviewCompositionMixin
from infrastructure.containers.work import WorkCompositionMixin


class Container(
    DocumentCompositionMixin,
    EventCompositionMixin,
    RemedialCompositionMixin,
    ReportingCompositionMixin,
    ReviewCompositionMixin,
    WorkCompositionMixin,
):
    """Wires pure use cases to Django infrastructure adapters."""

    def __init__(self):
        self._initialize_document_composition()
        self._initialize_event_composition()
        self._initialize_remedial_composition()
        self._initialize_reporting_composition()
        self._initialize_review_composition()
        self._initialize_work_composition()
        self._academic_year_catalog_repo = None
        self._academic_year_activation_repo = None
        self._student_catalog_repo = None
        self._student_command_repo = None
        self._student_group_catalog_repo = None
        self._student_group_command_repo = None
        self._student_import_snapshot_repo = None
        self._student_import_command_repo = None
        self._student_profile_repo = None
        self._source_catalog_repo = None
        self._source_command_repo = None
        self._task_read_repo = None
        self._task_command_repo = None
        self._task_classification_repo = None
        self._task_classification_backfill_repo = None
        self._task_image_command_repo = None
        self._task_lifecycle_command_repo = None
        self._task_selection_repo = None
        self._task_taxonomy_repo = None
        self._task_export_repo = None
        self._task_group_catalog_repo = None
        self._task_group_management_repo = None
        self._task_math_status_cache = None
        self._task_image_audit_query_repo = None
        self._task_image_audit_command_repo = None
        self._task_db_health_repo = None
        self._course_catalog_repo = None
        self._topic_catalog_repo = None
        self._curriculum_import_repo = None
        self._codifier_catalog_repo = None
        self._codifier_detail_repo = None
        self._codifier_import_repo = None
        self._dashboard_summary_repo = None
        self._global_search_repo = None
        self._import_log_repo = None
        self._site_settings_query_repo = None
        self._site_settings_command_repo = None
        self._codifier_form_adapter = None
        self._core_form_adapter = None
        self._curriculum_form_adapter = None
        self._settings_form_adapter = None
        self._student_form_adapter = None
        self._task_group_form_adapter = None
        self._task_form_adapter = None
        self._task_import_service = None
        self._transaction_manager = None

    @property
    def academic_year_catalog_repo(self):
        if self._academic_year_catalog_repo is None:
            self._academic_year_catalog_repo = (
                DjangoAcademicYearCatalogRepository()
            )
        return self._academic_year_catalog_repo

    @property
    def academic_year_activation_repo(self):
        if self._academic_year_activation_repo is None:
            self._academic_year_activation_repo = (
                DjangoAcademicYearActivationRepository()
            )
        return self._academic_year_activation_repo

    @property
    def student_catalog_repo(self):
        if self._student_catalog_repo is None:
            self._student_catalog_repo = DjangoStudentCatalogRepository()
        return self._student_catalog_repo

    @property
    def student_command_repo(self):
        if self._student_command_repo is None:
            self._student_command_repo = DjangoStudentCommandRepository()
        return self._student_command_repo

    @property
    def student_group_catalog_repo(self):
        if self._student_group_catalog_repo is None:
            self._student_group_catalog_repo = (
                DjangoStudentGroupCatalogRepository()
            )
        return self._student_group_catalog_repo

    @property
    def student_group_command_repo(self):
        if self._student_group_command_repo is None:
            self._student_group_command_repo = (
                DjangoStudentGroupCommandRepository()
            )
        return self._student_group_command_repo

    @property
    def student_import_snapshot_repo(self):
        if self._student_import_snapshot_repo is None:
            self._student_import_snapshot_repo = (
                DjangoStudentImportSnapshotRepository()
            )
        return self._student_import_snapshot_repo

    @property
    def student_import_command_repo(self):
        if self._student_import_command_repo is None:
            self._student_import_command_repo = (
                DjangoStudentImportCommandRepository()
            )
        return self._student_import_command_repo

    @property
    def student_profile_repo(self):
        if self._student_profile_repo is None:
            self._student_profile_repo = DjangoStudentProfileRepository()
        return self._student_profile_repo

    @property
    def source_catalog_repo(self):
        if self._source_catalog_repo is None:
            self._source_catalog_repo = DjangoSourceCatalogRepository()
        return self._source_catalog_repo

    @property
    def source_command_repo(self):
        if self._source_command_repo is None:
            self._source_command_repo = DjangoSourceCommandRepository()
        return self._source_command_repo

    @property
    def task_read_repo(self):
        if self._task_read_repo is None:
            self._task_read_repo = DjangoTaskReadRepository(
                math_status_cache=self.task_math_status_cache,
            )
        return self._task_read_repo

    @property
    def task_command_repo(self):
        if self._task_command_repo is None:
            self._task_command_repo = DjangoTaskCommandRepository()
        return self._task_command_repo

    @property
    def task_classification_repo(self):
        if self._task_classification_repo is None:
            self._task_classification_repo = (
                DjangoTaskClassificationRepository()
            )
        return self._task_classification_repo

    @property
    def task_classification_backfill_repo(self):
        if self._task_classification_backfill_repo is None:
            self._task_classification_backfill_repo = (
                DjangoTaskClassificationBackfillRepository()
            )
        return self._task_classification_backfill_repo

    @property
    def task_image_command_repo(self):
        if self._task_image_command_repo is None:
            self._task_image_command_repo = DjangoTaskImageCommandRepository()
        return self._task_image_command_repo

    @property
    def task_lifecycle_command_repo(self):
        if self._task_lifecycle_command_repo is None:
            self._task_lifecycle_command_repo = (
                DjangoTaskLifecycleCommandRepository()
            )
        return self._task_lifecycle_command_repo

    @property
    def task_selection_repo(self):
        if self._task_selection_repo is None:
            self._task_selection_repo = DjangoTaskSelectionRepository()
        return self._task_selection_repo

    @property
    def task_taxonomy_repo(self):
        if self._task_taxonomy_repo is None:
            self._task_taxonomy_repo = DjangoTaskTaxonomyRepository()
        return self._task_taxonomy_repo

    @property
    def task_export_repo(self):
        if self._task_export_repo is None:
            self._task_export_repo = DjangoTaskExportRepository()
        return self._task_export_repo

    @property
    def task_group_catalog_repo(self):
        if self._task_group_catalog_repo is None:
            self._task_group_catalog_repo = DjangoTaskGroupCatalogRepository()
        return self._task_group_catalog_repo

    @property
    def task_group_management_repo(self):
        if self._task_group_management_repo is None:
            self._task_group_management_repo = (
                DjangoTaskGroupManagementRepository()
            )
        return self._task_group_management_repo

    @property
    def task_math_status_cache(self):
        if self._task_math_status_cache is None:
            self._task_math_status_cache = task_math_status_cache
        return self._task_math_status_cache

    @property
    def task_image_audit_query_repo(self):
        if self._task_image_audit_query_repo is None:
            self._task_image_audit_query_repo = (
                DjangoTaskImageAuditQueryRepository()
            )
        return self._task_image_audit_query_repo

    @property
    def task_image_audit_command_repo(self):
        if self._task_image_audit_command_repo is None:
            self._task_image_audit_command_repo = (
                DjangoTaskImageAuditCommandRepository()
            )
        return self._task_image_audit_command_repo

    @property
    def transaction_manager(self):
        if self._transaction_manager is None:
            self._transaction_manager = DjangoTransactionManager()
        return self._transaction_manager

    @property
    def task_db_health_repo(self):
        if self._task_db_health_repo is None:
            self._task_db_health_repo = DjangoTaskDBHealthRepository()
        return self._task_db_health_repo

    @property
    def course_catalog_repo(self):
        if self._course_catalog_repo is None:
            self._course_catalog_repo = DjangoCourseCatalogRepository()
        return self._course_catalog_repo

    @property
    def topic_catalog_repo(self):
        if self._topic_catalog_repo is None:
            self._topic_catalog_repo = DjangoTopicCatalogRepository()
        return self._topic_catalog_repo

    @property
    def codifier_catalog_repo(self):
        if self._codifier_catalog_repo is None:
            self._codifier_catalog_repo = DjangoCodifierCatalogRepository()
        return self._codifier_catalog_repo

    @property
    def codifier_detail_repo(self):
        if self._codifier_detail_repo is None:
            self._codifier_detail_repo = DjangoCodifierDetailRepository()
        return self._codifier_detail_repo

    @property
    def codifier_import_repo(self):
        if self._codifier_import_repo is None:
            self._codifier_import_repo = DjangoCodifierImportRepository()
        return self._codifier_import_repo

    @property
    def curriculum_import_repo(self):
        if self._curriculum_import_repo is None:
            self._curriculum_import_repo = DjangoCurriculumImportRepository()
        return self._curriculum_import_repo

    @property
    def dashboard_summary_repo(self):
        if self._dashboard_summary_repo is None:
            self._dashboard_summary_repo = DjangoDashboardSummaryRepository()
        return self._dashboard_summary_repo

    @property
    def global_search_repo(self):
        if self._global_search_repo is None:
            self._global_search_repo = DjangoGlobalSearchRepository()
        return self._global_search_repo

    @property
    def import_log_repo(self):
        if self._import_log_repo is None:
            self._import_log_repo = DjangoImportLogRepository()
        return self._import_log_repo

    @property
    def site_settings_query_repo(self):
        if self._site_settings_query_repo is None:
            self._site_settings_query_repo = DjangoSiteSettingsQueryRepository()
        return self._site_settings_query_repo

    @property
    def site_settings_command_repo(self):
        if self._site_settings_command_repo is None:
            self._site_settings_command_repo = (
                DjangoSiteSettingsCommandRepository()
            )
        return self._site_settings_command_repo

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
    def task_form_adapter(self):
        if self._task_form_adapter is None:
            self._task_form_adapter = TaskFormAdapter()
        return self._task_form_adapter

    @property
    def task_import_service(self):
        if self._task_import_service is None:
            self._task_import_service = DjangoTaskImportService()
        return self._task_import_service

    def analytics_service(self):
        return StudentAnalyticsService()

    def get_student_profile_use_case(self):
        return GetStudentProfileUseCase(
            student_repo=self.student_catalog_repo,
            student_learning_repo=self.student_profile_repo,
            analytics_service=self.analytics_service(),
        )

    def get_student_detail_use_case(self):
        return GetStudentDetailUseCase(
            student_repo=self.student_catalog_repo,
        )

    def get_student_group_detail_use_case(self):
        return GetStudentGroupDetailUseCase(
            student_repo=self.student_group_catalog_repo,
        )

    def get_student_list_use_case(self):
        return GetStudentListUseCase(
            student_repo=self.student_catalog_repo,
        )

    def resolve_academic_year_use_case(self):
        return ResolveAcademicYearUseCase(
            academic_year_repo=self.academic_year_catalog_repo,
        )

    def get_academic_year_list_use_case(self):
        return GetAcademicYearListUseCase(
            academic_year_repo=self.academic_year_catalog_repo,
        )

    def activate_academic_year_use_case(self):
        return ActivateAcademicYearUseCase(
            academic_year_repo=self.academic_year_activation_repo,
        )

    def get_student_group_list_use_case(self):
        return GetStudentGroupListUseCase(
            student_repo=self.student_group_catalog_repo,
        )

    def create_student_use_case(self):
        return CreateStudentUseCase(
            student_repo=self.student_command_repo,
        )

    def update_student_use_case(self):
        return UpdateStudentUseCase(
            student_repo=self.student_command_repo,
        )

    def create_student_group_use_case(self):
        return CreateStudentGroupUseCase(
            student_repo=self.student_group_command_repo,
        )

    def update_student_group_use_case(self):
        return UpdateStudentGroupUseCase(
            student_repo=self.student_group_command_repo,
        )

    def import_students_use_case(self):
        return ImportStudentsUseCase(
            snapshot_repo=self.student_import_snapshot_repo,
            command_repo=self.student_import_command_repo,
            transaction_manager=self.transaction_manager,
        )

    def import_codifier_use_case(self):
        return ImportCodifierUseCase(
            codifier_repo=self.codifier_import_repo,
            transaction_manager=self.transaction_manager,
        )

    def import_curriculum_use_case(self):
        return ImportCurriculumUseCase(
            curriculum_repo=self.curriculum_import_repo,
            transaction_manager=self.transaction_manager,
        )

    def backfill_task_classifications_use_case(self):
        return BackfillTaskClassificationsUseCase(
            backfill_repo=self.task_classification_backfill_repo,
            transaction_manager=self.transaction_manager,
        )

    def get_task_list_use_case(self):
        return GetTaskListUseCase(
            task_repo=self.task_read_repo,
            task_catalog_repo=self.task_taxonomy_repo,
            task_group_repo=self.task_group_catalog_repo,
            math_status_cache=self.task_math_status_cache,
        )

    def get_task_group_list_use_case(self):
        return GetTaskGroupListUseCase(
            task_catalog_repo=self.task_taxonomy_repo,
            task_group_repo=self.task_group_catalog_repo,
        )

    def get_task_group_detail_use_case(self):
        return GetTaskGroupDetailUseCase(
            task_group_repo=self.task_group_catalog_repo,
        )

    def create_analog_group_use_case(self):
        return CreateAnalogGroupUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def update_analog_group_use_case(self):
        return UpdateAnalogGroupUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def get_add_tasks_to_group_use_case(self):
        return GetAddTasksToGroupUseCase(
            task_group_repo=self.task_group_catalog_repo,
        )

    def get_course_detail_use_case(self):
        return GetCourseDetailUseCase(
            curriculum_repo=self.course_catalog_repo,
        )

    def get_course_list_use_case(self):
        return GetCourseListUseCase(
            curriculum_repo=self.course_catalog_repo,
        )

    def get_topic_subtopics_use_case(self):
        return GetTopicSubtopicsUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_topic_list_use_case(self):
        return GetTopicListUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_topic_detail_use_case(self):
        return GetTopicDetailUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_codifier_list_use_case(self):
        return GetCodifierListUseCase(
            codifier_repo=self.codifier_catalog_repo,
        )

    def get_codifier_detail_use_case(self):
        return GetCodifierDetailUseCase(
            codifier_repo=self.codifier_detail_repo,
        )

    def get_dashboard_summary_use_case(self):
        return GetDashboardSummaryUseCase(
            core_repo=self.dashboard_summary_repo,
        )

    def get_global_search_use_case(self):
        return GetGlobalSearchUseCase(
            core_repo=self.global_search_repo,
        )

    def get_import_page_use_case(self):
        return GetImportPageUseCase(
            core_repo=self.import_log_repo,
        )

    def get_import_history_use_case(self):
        return GetImportHistoryUseCase(
            core_repo=self.import_log_repo,
        )

    def get_site_settings_use_case(self):
        return GetSiteSettingsUseCase(
            settings_repo=self.site_settings_query_repo,
        )

    def save_site_settings_use_case(self):
        return SaveSiteSettingsUseCase(
            settings_repo=self.site_settings_command_repo,
        )

    def validate_task_import_json_use_case(self):
        return ValidateTaskImportJsonUseCase()

    def execute_task_import_use_case(self):
        return ExecuteTaskImportUseCase(
            task_import_service=self.task_import_service,
            validate_json_use_case=self.validate_task_import_json_use_case(),
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
            task_repo=self.task_read_repo,
        )

    def get_subtopic_options_use_case(self):
        return GetSubtopicOptionsUseCase(
            task_catalog_repo=self.task_taxonomy_repo,
        )

    def get_task_classification_options_use_case(self):
        return GetTaskClassificationOptionsUseCase(
            classification_repo=self.task_classification_repo,
        )

    def get_source_list_use_case(self):
        return GetSourceListUseCase(
            source_repo=self.source_catalog_repo,
        )

    def create_source_use_case(self):
        return CreateSourceUseCase(
            source_repo=self.source_command_repo,
        )

    def refresh_task_math_cache_use_case(self):
        return RefreshTaskMathCacheUseCase(
            math_status_cache=self.task_math_status_cache,
        )

    def create_task_use_case(self):
        return CreateTaskUseCase(
            task_repo=self.task_command_repo,
            task_catalog_repo=self.task_taxonomy_repo,
            classification_repo=self.task_classification_repo,
        )

    def update_task_use_case(self):
        return UpdateTaskUseCase(
            task_repo=self.task_command_repo,
            task_catalog_repo=self.task_taxonomy_repo,
            classification_repo=self.task_classification_repo,
        )

    def save_task_images_use_case(self):
        return SaveTaskImagesUseCase(
            task_repo=self.task_image_command_repo,
        )

    def get_task_db_health_use_case(self):
        return GetTaskDBHealthUseCase(
            report_repo=self.task_db_health_repo,
        )

    def analyze_task_images_use_case(self):
        return AnalyzeTaskImagesUseCase(
            image_repo=self.task_image_audit_query_repo,
        )

    def apply_task_image_position_suggestions_use_case(self):
        return ApplyTaskImagePositionSuggestionsUseCase(
            image_repo=self.task_image_audit_command_repo,
        )

    def prepare_add_tasks_to_group_submission_use_case(self):
        return PrepareAddTasksToGroupSubmissionUseCase()

    def prepare_update_task_group_roles_submission_use_case(self):
        return PrepareUpdateTaskGroupRolesSubmissionUseCase()

    def delete_task_groups_use_case(self):
        return DeleteTaskGroupsUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def delete_task_use_case(self):
        return DeleteTaskUseCase(
            task_repo=self.task_lifecycle_command_repo,
        )

    def add_tasks_to_group_use_case(self):
        return AddTasksToGroupUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def remove_task_from_group_use_case(self):
        return RemoveTaskFromGroupUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def update_task_group_roles_use_case(self):
        return UpdateTaskGroupRolesUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def bulk_create_group_from_tasks_use_case(self):
        return BulkCreateGroupFromTasksUseCase(
            task_repo=self.task_selection_repo,
            task_group_repo=self.task_group_management_repo,
        )

    def bulk_add_tasks_to_group_use_case(self):
        return BulkAddTasksToGroupUseCase(
            task_repo=self.task_selection_repo,
            task_group_repo=self.task_group_management_repo,
        )

    def bulk_remove_tasks_from_groups_use_case(self):
        return BulkRemoveTasksFromGroupsUseCase(
            task_group_repo=self.task_group_management_repo,
        )

container = Container()
