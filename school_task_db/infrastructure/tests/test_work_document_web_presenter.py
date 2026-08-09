from unittest import TestCase

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    DocumentRenderResult,
    GeneratedDocumentFile,
)
from core_logic.value_objects.document_render_options import (
    RenderTarget,
    WorkDocumentPrintOverrides,
)
from infrastructure.presenters.work_document import WorkDocumentWebPresenter


class WorkDocumentWebPresenterTests(TestCase):
    def setUp(self):
        self.presenter = WorkDocumentWebPresenter()

    def test_presents_successful_work_document(self):
        response = self.presenter.work_document_response(
            self._result(
                renderer_type='html',
                filename='work.html',
                size_kb=1.25,
            ),
            RenderTarget(renderer_type='html'),
            WorkDocumentPrintOverrides(append_answers=True),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.payload, {
            'success': True,
            'message': (
                'HTML документ создан '
                '(по спецификации + ответы в конце)'
            ),
            'files': [{
                'name': 'work.html',
                'size': '1.2 KB',
                'download_url': '/works/download/html/work.html/',
            }],
            'total_files': 1,
        })

    def test_presents_missing_work_as_not_found(self):
        response = self.presenter.work_document_response(
            self._result(status=DOCUMENT_RENDER_STATUS_NOT_FOUND),
            RenderTarget(renderer_type='html'),
            WorkDocumentPrintOverrides(),
        )

        self.assertTrue(response.is_not_found)
        self.assertEqual(response.not_found_message, 'Работа не найдена')

    def test_presents_work_domain_rejections_as_bad_requests(self):
        statuses = (
            DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED,
            DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
        )

        for status in statuses:
            with self.subTest(status=status):
                response = self.presenter.work_document_response(
                    self._result(status=status, renderer_type='docx'),
                    RenderTarget(renderer_type='pdf'),
                    WorkDocumentPrintOverrides(),
                )
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.payload['success'])

    def test_presents_successful_personal_remedial_sheet(self):
        response = self.presenter.remedial_sheet_response(
            self._result(filename='remedial.pdf', size_kb=2.0),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.payload, {
            'status': 'success',
            'files': [{
                'filename': 'remedial.pdf',
                'url': '/works/download/pdf/remedial.pdf/',
            }],
            'message': 'Рабочий лист создан (PDF)',
        })

    def test_presents_invalid_personal_remedial_states(self):
        statuses = (
            DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
            DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
            DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
        )

        for status in statuses:
            with self.subTest(status=status):
                response = self.presenter.remedial_sheet_response(
                    self._result(status=status, renderer_type='docx'),
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.payload['status'], 'error')

    def test_presents_empty_personal_remedial_sheet_as_server_error(self):
        response = self.presenter.remedial_sheet_response(
            self._result(status=DOCUMENT_RENDER_STATUS_EMPTY),
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.payload['status'], 'error')

    def test_presents_successful_remedial_batch(self):
        response = self.presenter.remedial_sheet_batch_response(
            self._result(filename='remedial_work.pdf', size_kb=3.0),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.payload['total_files'], 1)
        self.assertEqual(
            response.payload['files'][0]['download_url'],
            '/works/download/pdf/remedial_work.pdf/',
        )

    def test_presents_empty_remedial_batch_as_bad_request(self):
        response = self.presenter.remedial_sheet_batch_response(
            self._result(status=DOCUMENT_RENDER_STATUS_EMPTY),
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.payload['success'])

    def test_presents_unexpected_failures_as_server_errors(self):
        result = self._result(status='failed')

        work_response = self.presenter.work_document_response(
            result,
            RenderTarget(renderer_type='pdf'),
            WorkDocumentPrintOverrides(),
        )
        remedial_response = self.presenter.remedial_sheet_response(result)
        batch_response = self.presenter.remedial_sheet_batch_response(result)

        self.assertEqual(work_response.status_code, 500)
        self.assertEqual(remedial_response.status_code, 500)
        self.assertEqual(batch_response.status_code, 500)

    @staticmethod
    def _result(
        status=DOCUMENT_RENDER_STATUS_GENERATED,
        renderer_type='pdf',
        filename='',
        size_kb=0.0,
    ):
        files = []
        if filename:
            files.append(
                GeneratedDocumentFile(filename=filename, size_kb=size_kb),
            )
        return DocumentRenderResult(
            status=status,
            renderer_type=renderer_type,
            file_type=renderer_type,
            files=files,
        )
