"""Django execution adapter for task-bank imports and previews."""

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.interfaces.task_import import ITaskImportRunner
from core_logic.services.task_import_preview_service import (
    TaskImportPreviewService,
)
from infrastructure.importers.tasks import TaskImporter
from infrastructure.repositories.django_task_import_preview_repo import (
    DjangoTaskImportPreviewRepository,
)


class DjangoTaskImportRunner(ITaskImportRunner):
    def __init__(
        self,
        preview_repo=None,
        preview_service=None,
    ):
        self.preview_repo = preview_repo or DjangoTaskImportPreviewRepository()
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
        importer = TaskImporter(
            mode=request.mode,
            verbose=True,
            create_missing=request.create_missing,
            output=lambda _message: None,
        )
        return importer.import_tasks_from_json(request.data)

    def _preview(self, data) -> TaskImportRunSummary:
        lookup = self.preview_service.build_lookup(data)
        facts = self.preview_repo.get_facts(lookup)
        return TaskImportRunSummary(
            preview=self.preview_service.build(data, facts),
        )
