from types import SimpleNamespace
from unittest import TestCase

from infrastructure.services.report_document_payloads import (
    EventReportDocumentDataProvider,
    EventReportSectionPayloadBuilder,
    StudentDigestDocumentDataProvider,
    StudentDigestSectionPayloadBuilder,
)


class ReportDocumentPayloadTests(TestCase):
    def test_event_report_is_loaded_once_per_document_build(self):
        calls = []
        report = object()
        provider = EventReportDocumentDataProvider(
            lambda event_id: calls.append(event_id) or report,
        )
        builder = EventReportSectionPayloadBuilder(provider)
        build_context = {}
        request = self._request(
            source_id='event-1',
            options={'show_codes': True},
            build_context=build_context,
        )

        first = builder.build_payload(request)
        second = builder.build_payload(request)
        builder.build_payload(
            self._request(source_id='event-1', build_context={}),
        )

        self.assertIs(first['report'], report)
        self.assertIs(second['report'], report)
        self.assertEqual(first['options'], {'show_codes': True})
        self.assertEqual(calls, ['event-1', 'event-1'])

    def test_student_digest_selects_requested_student_from_cached_page(self):
        calls = []
        digest_request = object()
        first_digest = self._digest('student-1')
        selected_digest = self._digest('student-2')
        page = SimpleNamespace(digests=(first_digest, selected_digest))
        provider = StudentDigestDocumentDataProvider(
            lambda request: calls.append(request) or page,
        )
        builder = StudentDigestSectionPayloadBuilder(provider)
        request = self._request(
            options={
                'digest_request': digest_request,
                'student_id': 'student-2',
            },
        )

        payload = builder.build_payload(request)
        repeated = builder.build_payload(request)

        self.assertIs(payload['page'], page)
        self.assertIs(payload['digest'], selected_digest)
        self.assertIs(repeated['digest'], selected_digest)
        self.assertEqual(calls, [digest_request])

    def test_student_digest_requires_digest_request(self):
        provider = StudentDigestDocumentDataProvider(lambda request: object())

        with self.assertRaisesRegex(ValueError, 'Digest request is required'):
            provider.get_page(self._request())

    @staticmethod
    def _digest(student_id):
        return SimpleNamespace(
            student=SimpleNamespace(pk=student_id),
        )

    @staticmethod
    def _request(source_id='', options=None, build_context=None):
        return SimpleNamespace(
            source=SimpleNamespace(source_id=source_id),
            section=SimpleNamespace(options=options or {}),
            build_context=(
                build_context if build_context is not None else {}
            ),
        )
