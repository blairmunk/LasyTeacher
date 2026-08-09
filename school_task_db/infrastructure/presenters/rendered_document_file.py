"""Django responses for files produced by the document engine."""

from django.http import HttpResponse

from core_logic.entities.document_rendering import (
    GENERATED_FILE_STATUS_NOT_FOUND,
    GENERATED_FILE_STATUS_UNSUPPORTED_TYPE,
)


class RenderedDocumentFilePresenter:
    @staticmethod
    def response(result, disposition='attachment'):
        if not result.success or result.file is None:
            return None

        response = HttpResponse(
            result.file.content,
            content_type=result.file.content_type,
        )
        response['Content-Disposition'] = (
            f'{disposition}; filename="{result.file.filename}"'
        )
        return response

    @staticmethod
    def download_error_message(result):
        if result.status == GENERATED_FILE_STATUS_UNSUPPORTED_TYPE:
            return 'Неподдерживаемый тип файла'
        if result.status == GENERATED_FILE_STATUS_NOT_FOUND:
            return 'Файл не найден'
        return 'Ошибка чтения файла'
