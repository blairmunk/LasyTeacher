"""Prepare uploaded JSON content for task import."""

import json

from core_logic.entities.task_import import (
    TaskImportFileRequest,
    TaskImportFileResult,
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
