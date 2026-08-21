"""Django adapter for the legacy task import components."""

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.interfaces.task_import import ITaskImportRunner
from infrastructure.importers.tasks import TaskImporter


class DjangoTaskImportRunner(ITaskImportRunner):
    def preview_import(
        self,
        request: TaskImportPreviewRequest,
    ) -> TaskImportRunSummary:
        return self._run_import(
            data=request.data,
            mode='update',
            dry_run=True,
            verbose=False,
            create_missing=True,
        )

    def execute_import(
        self,
        request: TaskImportRequest,
    ) -> TaskImportRunSummary:
        return self._run_import(
            data=request.data,
            mode=request.mode,
            dry_run=request.dry_run,
            verbose=True,
            create_missing=request.create_missing,
        )

    @staticmethod
    def _run_import(*, data, mode, dry_run, verbose, create_missing):
        importer = TaskImporter(
            mode=mode,
            dry_run=dry_run,
            verbose=verbose,
            create_missing=create_missing,
            output=lambda _message: None,
        )
        return importer.import_tasks_from_json(data)
