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
        importer, context = self._run_import(
            data=request.data,
            mode='update',
            dry_run=True,
            verbose=False,
            create_missing=True,
        )
        return self._summary(importer, context)

    def execute_import(
        self,
        request: TaskImportRequest,
    ) -> TaskImportRunSummary:
        importer, context = self._run_import(
            data=request.data,
            mode=request.mode,
            dry_run=request.dry_run,
            verbose=True,
            create_missing=request.create_missing,
        )
        return self._summary(importer, context)

    @staticmethod
    def _run_import(*, data, mode, dry_run, verbose, create_missing):
        importer = TaskImporter(
            mode=mode,
            dry_run=dry_run,
            verbose=verbose,
            create_missing=create_missing,
            output=lambda _message: None,
        )
        importer.validate_mode()
        context = importer.import_tasks_from_json(data)
        return importer, context

    @staticmethod
    def _summary(importer, context) -> TaskImportRunSummary:
        return TaskImportRunSummary(
            created_by_type=dict(importer.stats.created_by_type),
            updated_by_type=dict(importer.stats.updated_by_type),
            skipped_by_type=dict(importer.stats.skipped_by_type),
            errors=getattr(importer.stats, 'errors', 0),
            error_messages=tuple(
                str(error.get('message', error))
                for error in getattr(
                    importer.stats,
                    'error_details',
                    (),
                )[:50]
            ),
            context_counts=context.get_stats_summary(),
            preview=context.preview_summary,
        )
