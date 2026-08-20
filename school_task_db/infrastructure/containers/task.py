"""Task bank and task group wiring for the dependency container."""

from core_logic.use_cases.analyze_task_images import (
    AnalyzeTaskImagesUseCase,
    ApplyTaskImagePositionSuggestionsUseCase,
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
from core_logic.use_cases.delete_task import DeleteTaskUseCase
from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsUseCase
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase
from core_logic.use_cases.execute_task_import_submission import (
    ExecuteTaskImportSubmissionUseCase,
)
from core_logic.use_cases.export_tasks import ExportTasksUseCase
from core_logic.use_cases.get_add_tasks_to_group import GetAddTasksToGroupUseCase
from core_logic.use_cases.get_source_list import GetSourceListUseCase
from core_logic.use_cases.get_task_classification_options import (
    GetTaskClassificationOptionsUseCase,
)
from core_logic.use_cases.get_task_db_health import GetTaskDBHealthUseCase
from core_logic.use_cases.get_task_detail import GetTaskDetailUseCase
from core_logic.use_cases.get_task_group_detail import GetTaskGroupDetailUseCase
from core_logic.use_cases.get_task_group_list import GetTaskGroupListUseCase
from core_logic.use_cases.get_task_import_sample import GetTaskImportSampleUseCase
from core_logic.use_cases.get_task_list import GetTaskListUseCase
from core_logic.use_cases.get_task_reference_options import (
    GetSubtopicOptionsUseCase,
)
from core_logic.use_cases.prepare_task_group_membership_submission import (
    PrepareAddTasksToGroupSubmissionUseCase,
    PrepareUpdateTaskGroupRolesSubmissionUseCase,
)
from core_logic.use_cases.prepare_task_import_file import (
    PrepareTaskImportExecutionSubmissionUseCase,
    PrepareTaskImportFileUseCase,
)
from core_logic.use_cases.preview_task_import import PreviewTaskImportUseCase
from core_logic.use_cases.preview_task_import_file import (
    PreviewTaskImportFileUseCase,
)
from core_logic.use_cases.refresh_task_math_cache import RefreshTaskMathCacheUseCase
from core_logic.use_cases.save_analog_group import (
    CreateAnalogGroupUseCase,
    UpdateAnalogGroupUseCase,
)
from core_logic.use_cases.save_task import (
    CreateTaskUseCase,
    SaveTaskImagesUseCase,
    UpdateTaskUseCase,
)
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonUseCase,
)
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter
from infrastructure.repositories.django_source_catalog_repo import (
    DjangoSourceCatalogRepository,
)
from infrastructure.repositories.django_source_command_repo import (
    DjangoSourceCommandRepository,
)
from infrastructure.repositories.django_task_classification_backfill_repo import (
    DjangoTaskClassificationBackfillRepository,
)
from infrastructure.repositories.django_task_classification_repo import (
    DjangoTaskClassificationRepository,
)
from infrastructure.repositories.django_task_command_repo import (
    DjangoTaskCommandRepository,
)
from infrastructure.repositories.django_task_db_health_repo import (
    DjangoTaskDBHealthRepository,
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
from infrastructure.repositories.django_task_image_command_repo import (
    DjangoTaskImageCommandRepository,
)
from infrastructure.repositories.django_task_lifecycle_command_repo import (
    DjangoTaskLifecycleCommandRepository,
)
from infrastructure.repositories.django_task_read_repo import (
    DjangoTaskReadRepository,
)
from infrastructure.repositories.django_task_selection_repo import (
    DjangoTaskSelectionRepository,
)
from infrastructure.repositories.django_task_taxonomy_repo import (
    DjangoTaskTaxonomyRepository,
)
from infrastructure.services.task_import_service import DjangoTaskImportService
from infrastructure.services.task_math_status_cache import task_math_status_cache


class TaskCompositionMixin:
    """Owns task bank, source, image, import, and group wiring."""

    def _initialize_task_composition(self):
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
        self._task_group_form_adapter = None
        self._task_form_adapter = None
        self._task_import_service = None

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
    def task_db_health_repo(self):
        if self._task_db_health_repo is None:
            self._task_db_health_repo = DjangoTaskDBHealthRepository()
        return self._task_db_health_repo

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
