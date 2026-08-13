import datetime as dt
from unittest import TestCase

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.student_digest import (
    StudentDigestOptions,
    StudentDigestPageData,
    StudentDigestRequest,
)
from core_logic.use_cases.get_student_digest_page import (
    GetStudentDigestPageUseCase,
    StudentDigestPageRequest,
)


class DigestUseCaseStub:
    def __init__(self, page):
        self.page = page
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        if (
            request.start_date
            and request.end_date
            and request.start_date > request.end_date
        ):
            raise ValueError('Начало периода не может быть позже окончания.')
        return self.page


class GetStudentDigestPageUseCaseTests(TestCase):
    def test_returns_requested_page_without_fallback(self):
        page = self._page()
        digest_use_case = DigestUseCaseStub(page)
        digest_request = StudentDigestRequest(
            start_date=dt.date(2026, 8, 1),
            end_date=dt.date(2026, 8, 8),
        )

        result = GetStudentDigestPageUseCase(digest_use_case).execute(
            StudentDigestPageRequest(
                digest_request=digest_request,
                fallback_end_date=dt.date(2026, 8, 13),
            ),
        )

        self.assertIs(result.page, page)
        self.assertEqual(result.form_error, '')
        self.assertEqual(digest_use_case.requests, [digest_request])

    def test_recovers_reversed_period_with_default_unfiltered_request(self):
        page = self._page()
        digest_use_case = DigestUseCaseStub(page)
        year = AcademicYearRef(
            pk='year-1',
            name='2026-2027',
            start_date=dt.date(2026, 9, 1),
            end_date=dt.date(2027, 8, 31),
        )

        result = GetStudentDigestPageUseCase(digest_use_case).execute(
            StudentDigestPageRequest(
                digest_request=StudentDigestRequest(
                    group_id='group-1',
                    student_id='student-1',
                    start_date=dt.date(2026, 8, 10),
                    end_date=dt.date(2026, 8, 1),
                    year=year,
                ),
                fallback_end_date=dt.date(2026, 8, 13),
            ),
        )

        fallback = digest_use_case.requests[1]
        self.assertIs(result.page, page)
        self.assertIn('Начало периода', result.form_error)
        self.assertEqual(fallback.start_date, dt.date(2026, 8, 6))
        self.assertEqual(fallback.end_date, dt.date(2026, 8, 13))
        self.assertEqual(fallback.year, year)
        self.assertEqual(fallback.group_id, '')
        self.assertEqual(fallback.student_id, '')

    @staticmethod
    def _page():
        return StudentDigestPageData(
            groups=(),
            selected_group=None,
            start_date=dt.date(2026, 8, 6),
            end_date=dt.date(2026, 8, 13),
            options=StudentDigestOptions(),
        )
