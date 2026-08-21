"""Preview task import through the application runner port."""

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportPreviewResult,
)
from core_logic.interfaces.task_import import ITaskImportRunner


class PreviewTaskImportUseCase:
    def __init__(self, task_import_runner: ITaskImportRunner):
        self.task_import_runner = task_import_runner

    def execute(
        self,
        request: TaskImportPreviewRequest,
    ) -> TaskImportPreviewResult:
        try:
            summary = self.task_import_runner.preview_import(request)
        except Exception as error:
            return TaskImportPreviewResult(
                warning=f'Ошибка dry-run: {error}',
            )
        return TaskImportPreviewResult(preview=dict(summary.preview))
