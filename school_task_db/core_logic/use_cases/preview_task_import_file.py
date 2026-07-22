"""Validate an uploaded task import file and build a dry-run preview."""

from core_logic.entities.task_import import (
    TaskImportFileRequest,
    TaskImportPreviewRequest,
    TaskImportValidationPreviewResult,
)
from core_logic.use_cases.prepare_task_import_file import (
    PrepareTaskImportFileUseCase,
)
from core_logic.use_cases.preview_task_import import PreviewTaskImportUseCase
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonRequest,
    ValidateTaskImportJsonUseCase,
)


class PreviewTaskImportFileUseCase:
    def __init__(
        self,
        preview_task_import_use_case: PreviewTaskImportUseCase,
        prepare_file_use_case: PrepareTaskImportFileUseCase | None = None,
        validate_json_use_case: ValidateTaskImportJsonUseCase | None = None,
    ):
        self.preview_task_import_use_case = preview_task_import_use_case
        self.prepare_file_use_case = (
            prepare_file_use_case or PrepareTaskImportFileUseCase()
        )
        self.validate_json_use_case = (
            validate_json_use_case or ValidateTaskImportJsonUseCase()
        )

    def execute(
        self,
        request: TaskImportFileRequest,
    ) -> TaskImportValidationPreviewResult:
        prepared_file = self.prepare_file_use_case.execute(request)
        if not prepared_file.success:
            return TaskImportValidationPreviewResult(
                filename=prepared_file.filename,
                file_size=prepared_file.file_size,
                error=prepared_file.error,
            )

        validation = self.validate_json_use_case.execute(
            ValidateTaskImportJsonRequest(data=prepared_file.data),
        ).to_dict()

        preview = None
        if validation['is_valid']:
            preview_result = self.preview_task_import_use_case.execute(
                TaskImportPreviewRequest(data=prepared_file.data),
            )
            preview = preview_result.preview
            if not preview_result.success:
                validation['warnings'].append(preview_result.warning)

        return TaskImportValidationPreviewResult(
            filename=prepared_file.filename,
            file_size=prepared_file.file_size,
            validation=validation,
            preview=preview,
        )
