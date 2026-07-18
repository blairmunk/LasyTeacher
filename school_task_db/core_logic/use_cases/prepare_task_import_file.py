"""Prepare uploaded JSON content for task import."""

import json

from core_logic.entities.task_import import (
    TaskImportExecutionSubmissionRequest,
    TaskImportExecutionSubmissionResult,
    TaskImportFileRequest,
    TaskImportFileResult,
    TaskImportRequest,
)


MAX_TASK_IMPORT_FILE_SIZE = 50 * 1024 * 1024


class PrepareTaskImportFileUseCase:
    def execute(self, request: TaskImportFileRequest) -> TaskImportFileResult:
        if request.file_size > MAX_TASK_IMPORT_FILE_SIZE:
            size_mb = request.file_size // 1024 // 1024
            return TaskImportFileResult(
                filename=request.filename,
                file_size=request.file_size,
                error=f'Файл слишком большой: {size_mb}MB (макс: 50MB)',
            )

        try:
            raw_content = request.content.decode('utf-8')
            data = json.loads(raw_content)
        except UnicodeDecodeError:
            return TaskImportFileResult(
                filename=request.filename,
                file_size=request.file_size,
                error='Файл не в кодировке UTF-8',
            )
        except json.JSONDecodeError as exc:
            return TaskImportFileResult(
                filename=request.filename,
                file_size=request.file_size,
                error=(
                    f'Невалидный JSON: {exc.msg} '
                    f'(строка {exc.lineno}, позиция {exc.colno})'
                ),
            )

        return TaskImportFileResult(
            filename=request.filename,
            file_size=request.file_size,
            data=data,
        )


class PrepareTaskImportExecutionSubmissionUseCase:
    def __init__(self):
        self.file_use_case = PrepareTaskImportFileUseCase()

    def execute(
        self,
        request: TaskImportExecutionSubmissionRequest,
    ) -> TaskImportExecutionSubmissionResult:
        prepared_file = self.file_use_case.execute(
            TaskImportFileRequest(
                filename=request.filename,
                file_size=request.file_size,
                content=request.content,
            )
        )
        if not prepared_file.success:
            return TaskImportExecutionSubmissionResult(error=prepared_file.error)

        return TaskImportExecutionSubmissionResult(
            import_request=TaskImportRequest(
                data=prepared_file.data,
                filename=prepared_file.filename,
                file_size=prepared_file.file_size,
                mode=_first(request.form_data, 'mode', 'update'),
                dry_run=_first(request.form_data, 'dry_run') == 'true',
                create_missing=_first(
                    request.form_data,
                    'create_missing',
                    'true',
                ) == 'true',
            ),
        )


def _first(data, key: str, default: str = '') -> str:
    values = data.get(key)
    if not values:
        return default
    return str(values[0])
