from unittest import TestCase

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
    GeneratedDocumentFile,
)
from infrastructure.presenters.report_document import (
    ReportDocumentWebPresenter,
)


class ReportDocumentWebPresenterTests(TestCase):
    def setUp(self):
        self.presenter = ReportDocumentWebPresenter()

    def test_presents_generated_event_report_file(self):
        presentation = self.presenter.event_report(self._generated_result())

        self.assertTrue(presentation.has_file)
        self.assertEqual(presentation.file_type, 'html')
        self.assertEqual(presentation.filename, 'report.html')

    def test_presents_missing_event(self):
        presentation = self.presenter.event_report(
            self._result(DOCUMENT_RENDER_STATUS_NOT_FOUND),
        )

        self.assertTrue(presentation.is_not_found)
        self.assertEqual(
            presentation.not_found_message,
            'Событие не найдено.',
        )

    def test_presents_failed_event_report(self):
        presentation = self.presenter.event_report(self._result('failed'))

        self.assertFalse(presentation.has_file)
        self.assertEqual(
            presentation.error_message,
            'Не удалось сформировать документ отчёта.',
        )

    def test_presents_generated_student_digest_file(self):
        presentation = self.presenter.student_digest(self._generated_result())

        self.assertTrue(presentation.has_file)
        self.assertEqual(presentation.filename, 'report.html')

    def test_presents_missing_student_group(self):
        presentation = self.presenter.student_digest(
            self._result(DOCUMENT_RENDER_STATUS_NOT_FOUND),
        )

        self.assertTrue(presentation.is_not_found)
        self.assertEqual(presentation.not_found_message, 'Класс не найден.')

    def test_presents_empty_student_digest(self):
        presentation = self.presenter.student_digest(
            self._result(DOCUMENT_RENDER_STATUS_EMPTY),
        )

        self.assertFalse(presentation.has_file)
        self.assertEqual(
            presentation.error_message,
            'За выбранный период нет данных для печати.',
        )

    def test_generated_status_without_files_is_an_error(self):
        presentation = self.presenter.student_digest(
            self._result(DOCUMENT_RENDER_STATUS_GENERATED),
        )

        self.assertFalse(presentation.has_file)
        self.assertEqual(
            presentation.error_message,
            'Не удалось сформировать дайджесты.',
        )

    @staticmethod
    def _result(status):
        return DocumentRenderResult(status=status, renderer_type='html')

    @staticmethod
    def _generated_result():
        return DocumentRenderResult(
            status=DOCUMENT_RENDER_STATUS_GENERATED,
            renderer_type='html',
            file_type='html',
            files=[
                GeneratedDocumentFile(
                    filename='report.html',
                    size_kb=1.0,
                ),
            ],
        )
