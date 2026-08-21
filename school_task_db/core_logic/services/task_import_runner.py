"""Application runner coordinating task import preview and persistence."""

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.interfaces.task_import import (
    ITaskImportPreviewRepository,
    ITaskImportRunner,
    ITaskImportWriteSessionFactory,
)
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.services.task_import_preview_service import (
    TaskImportPreviewService,
)
from core_logic.use_cases.apply_task_import import ApplyTaskImportUseCase


class TaskImportRunnerService(ITaskImportRunner):
    def __init__(
        self,
        *,
        write_session_factory: ITaskImportWriteSessionFactory,
        preview_repo: ITaskImportPreviewRepository,
        transaction_manager: ITransactionManager,
        preview_service: TaskImportPreviewService | None = None,
    ):
        self.write_session_factory = write_session_factory
        self.preview_repo = preview_repo
        self.transaction_manager = transaction_manager
        self.preview_service = preview_service or TaskImportPreviewService()

    def preview_import(
        self,
        request: TaskImportPreviewRequest,
    ) -> TaskImportRunSummary:
        return self._preview(request.data)

    def execute_import(
        self,
        request: TaskImportRequest,
    ) -> TaskImportRunSummary:
        if request.dry_run:
            return self._preview(request.data)

        write_session = self.write_session_factory.create(
            mode=request.mode,
            create_missing=request.create_missing,
        )
        return ApplyTaskImportUseCase(
            write_session=write_session,
            transaction_manager=self.transaction_manager,
        ).execute(request)

    def _preview(self, data) -> TaskImportRunSummary:
        lookup = self.preview_service.build_lookup(data)
        facts = self.preview_repo.get_facts(lookup)
        return TaskImportRunSummary(
            preview=self.preview_service.build(data, facts),
        )
