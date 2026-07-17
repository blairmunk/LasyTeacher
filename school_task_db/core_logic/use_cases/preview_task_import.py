"""Preview task import."""

from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportPreviewResult,
)
from core_logic.interfaces.task_import import ITaskImportService


class PreviewTaskImportUseCase:
    def __init__(self, task_import_service: ITaskImportService):
        self.task_import_service = task_import_service

    def execute(self, request: TaskImportPreviewRequest) -> TaskImportPreviewResult:
        return self.task_import_service.preview_import(request)
