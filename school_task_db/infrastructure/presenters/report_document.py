"""Web presentation for report and student digest document results."""

from dataclasses import dataclass

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
)


@dataclass(frozen=True)
class ReportDocumentPresentation:
    file_type: str = ''
    filename: str = ''
    not_found_message: str = ''
    error_message: str = ''

    @property
    def has_file(self) -> bool:
        return bool(self.file_type and self.filename)

    @property
    def is_not_found(self) -> bool:
        return bool(self.not_found_message)


class ReportDocumentWebPresenter:
    def event_report(self, result) -> ReportDocumentPresentation:
        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            return ReportDocumentPresentation(
                not_found_message='Событие не найдено.',
            )
        return self._file_or_error(
            result,
            error_message='Не удалось сформировать документ отчёта.',
        )

    def student_digest(self, result) -> ReportDocumentPresentation:
        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            return ReportDocumentPresentation(
                not_found_message='Класс не найден.',
            )
        if result.status == DOCUMENT_RENDER_STATUS_EMPTY:
            return ReportDocumentPresentation(
                error_message='За выбранный период нет данных для печати.',
            )
        return self._file_or_error(
            result,
            error_message='Не удалось сформировать дайджесты.',
        )

    @staticmethod
    def _file_or_error(result, error_message):
        if result.success and result.files:
            return ReportDocumentPresentation(
                file_type=result.file_type,
                filename=result.files[0].filename,
                error_message=error_message,
            )
        return ReportDocumentPresentation(error_message=error_message)
