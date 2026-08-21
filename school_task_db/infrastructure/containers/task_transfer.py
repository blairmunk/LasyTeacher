"""Task import and export wiring for the dependency container."""

from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase
from core_logic.use_cases.execute_task_import_submission import (
    ExecuteTaskImportSubmissionUseCase,
)
from core_logic.use_cases.export_tasks import ExportTasksUseCase
from core_logic.use_cases.get_task_import_sample import GetTaskImportSampleUseCase
from core_logic.use_cases.prepare_task_import_file import (
    PrepareTaskImportExecutionSubmissionUseCase,
    PrepareTaskImportFileUseCase,
)
from core_logic.use_cases.preview_task_import import PreviewTaskImportUseCase
from core_logic.use_cases.preview_task_import_file import (
    PreviewTaskImportFileUseCase,
)
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonUseCase,
)
from infrastructure.repositories.django_task_export_repo import (
    DjangoTaskExportRepository,
)
from infrastructure.repositories.django_task_import_log_repo import (
    DjangoTaskImportLogRepository,
)
from infrastructure.repositories.django_task_import_preview_repo import (
    DjangoTaskImportPreviewRepository,
)
from infrastructure.services.django_task_import_runner import (
    DjangoTaskImportRunner,
)


class TaskTransferCompositionMixin:
    """Owns task import, preview, validation, and export wiring."""

    def _initialize_task_transfer_composition(self):
        self._task_export_repo = None
        self._task_import_runner = None
        self._task_import_log_repo = None
        self._task_import_preview_repo = None

    @property
    def task_export_repo(self):
        if self._task_export_repo is None:
            self._task_export_repo = DjangoTaskExportRepository()
        return self._task_export_repo

    @property
    def task_import_runner(self):
        if self._task_import_runner is None:
            self._task_import_runner = DjangoTaskImportRunner(
                preview_repo=self.task_import_preview_repo,
                transaction_manager=self.transaction_manager,
            )
        return self._task_import_runner

    @property
    def task_import_log_repo(self):
        if self._task_import_log_repo is None:
            self._task_import_log_repo = DjangoTaskImportLogRepository()
        return self._task_import_log_repo

    @property
    def task_import_preview_repo(self):
        if self._task_import_preview_repo is None:
            self._task_import_preview_repo = (
                DjangoTaskImportPreviewRepository()
            )
        return self._task_import_preview_repo

    def validate_task_import_json_use_case(self):
        return ValidateTaskImportJsonUseCase()

    def execute_task_import_use_case(self):
        return ExecuteTaskImportUseCase(
            task_import_runner=self.task_import_runner,
            task_import_log_repo=self.task_import_log_repo,
            validate_json_use_case=self.validate_task_import_json_use_case(),
        )

    def execute_task_import_submission_use_case(self):
        return ExecuteTaskImportSubmissionUseCase(
            execute_import_use_case=self.execute_task_import_use_case(),
        )

    def preview_task_import_use_case(self):
        return PreviewTaskImportUseCase(
            task_import_runner=self.task_import_runner,
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
