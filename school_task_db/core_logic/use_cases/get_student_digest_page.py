"""Build the interactive digest page with a recoverable date fallback."""

from dataclasses import dataclass
from datetime import date, timedelta

from core_logic.entities.student_digest import (
    StudentDigestPageData,
    StudentDigestRequest,
)
from core_logic.use_cases.get_student_digests import GetStudentDigestsUseCase


@dataclass(frozen=True)
class StudentDigestPageRequest:
    digest_request: StudentDigestRequest
    fallback_end_date: date


@dataclass(frozen=True)
class StudentDigestPageResult:
    page: StudentDigestPageData
    form_error: str = ''


class GetStudentDigestPageUseCase:
    def __init__(self, get_student_digests_use_case: GetStudentDigestsUseCase):
        self.get_student_digests_use_case = get_student_digests_use_case

    def execute(
        self,
        request: StudentDigestPageRequest,
    ) -> StudentDigestPageResult:
        try:
            page = self.get_student_digests_use_case.execute(
                request.digest_request,
            )
            return StudentDigestPageResult(page=page)
        except ValueError as error:
            fallback_request = StudentDigestRequest(
                start_date=request.fallback_end_date - timedelta(days=7),
                end_date=request.fallback_end_date,
                year=request.digest_request.year,
            )
            page = self.get_student_digests_use_case.execute(fallback_request)
            return StudentDigestPageResult(
                page=page,
                form_error=str(error),
            )
