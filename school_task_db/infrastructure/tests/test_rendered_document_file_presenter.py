from django.test import SimpleTestCase

from core_logic.entities.document_rendering import (
    GENERATED_FILE_STATUS_NOT_FOUND,
    GENERATED_FILE_STATUS_READ_ERROR,
    GENERATED_FILE_STATUS_READY,
    GENERATED_FILE_STATUS_UNSUPPORTED_TYPE,
    GeneratedFile,
    GeneratedFileResult,
)
from infrastructure.presenters.rendered_document_file import (
    RenderedDocumentFilePresenter,
)


class RenderedDocumentFilePresenterTests(SimpleTestCase):
    def setUp(self):
        self.presenter = RenderedDocumentFilePresenter()
        self.result = GeneratedFileResult(
            status=GENERATED_FILE_STATUS_READY,
            file=GeneratedFile(
                filename='report.html',
                content=b'<html>report</html>',
                content_type='text/html',
            ),
        )

    def test_builds_attachment_response(self):
        response = self.presenter.response(
            self.result,
            disposition='attachment',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'<html>report</html>')
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="report.html"',
        )

    def test_builds_inline_response(self):
        response = self.presenter.response(
            self.result,
            disposition='inline',
        )

        self.assertEqual(
            response['Content-Disposition'],
            'inline; filename="report.html"',
        )

    def test_returns_none_when_file_is_unavailable(self):
        response = self.presenter.response(
            GeneratedFileResult(status=GENERATED_FILE_STATUS_READ_ERROR),
        )

        self.assertIsNone(response)

    def test_maps_download_errors_to_user_messages(self):
        expected_messages = {
            GENERATED_FILE_STATUS_UNSUPPORTED_TYPE: (
                'Неподдерживаемый тип файла'
            ),
            GENERATED_FILE_STATUS_NOT_FOUND: 'Файл не найден',
            GENERATED_FILE_STATUS_READ_ERROR: 'Ошибка чтения файла',
        }

        for status, expected_message in expected_messages.items():
            with self.subTest(status=status):
                result = GeneratedFileResult(status=status)
                self.assertEqual(
                    self.presenter.download_error_message(result),
                    expected_message,
                )
