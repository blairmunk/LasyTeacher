"""Get customizable printable student digests for a group."""

from datetime import date, timedelta

from core_logic.entities.student_digest import (
    StudentDigestPageData,
    StudentDigestRequest,
)
from core_logic.interfaces.student_digest_repo import IStudentDigestRepository
from core_logic.services.student_digest_service import StudentDigestService


class GetStudentDigestsUseCase:
    def __init__(self, digest_repo, digest_service=None):
        self.digest_repo: IStudentDigestRepository = digest_repo
        self.digest_service = digest_service or StudentDigestService()

    def execute(self, request: StudentDigestRequest) -> StudentDigestPageData:
        end_date = request.end_date or date.today()
        start_date = request.start_date or end_date - timedelta(days=7)
        if start_date > end_date:
            raise ValueError('Начало периода не может быть позже окончания.')

        groups = self.digest_repo.get_digest_groups(request.year)
        selected_group = next(
            (group for group in groups if group.pk == request.group_id),
            None,
        )
        digests = ()
        if selected_group:
            source = self.digest_repo.get_student_digest_source(
                group_id=selected_group.pk,
                start_date=start_date,
                end_date=end_date,
            )
            if source:
                digests = self.digest_service.build(source, request.options)

        return StudentDigestPageData(
            groups=groups,
            selected_group=selected_group,
            start_date=start_date,
            end_date=end_date,
            options=request.options,
            digests=digests,
        )
