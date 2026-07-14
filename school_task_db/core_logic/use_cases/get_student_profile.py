"""Build student profile page data."""

from core_logic.interfaces.student_repo import IStudentRepository
from core_logic.services.analytics_service import (
    StudentAnalyticsService,
    StudentProfileData,
)


class GetStudentProfileUseCase:
    def __init__(
        self,
        student_repo: IStudentRepository,
        analytics_service: StudentAnalyticsService,
    ):
        self.student_repo = student_repo
        self.analytics_service = analytics_service

    def execute(self, student_id: str) -> StudentProfileData:
        participations = self.student_repo.get_profile_participations(student_id)
        work_ids = [
            participation.work.pk
            for participation in participations
            if participation.work and participation.score is not None
        ]

        return self.analytics_service.build_profile(
            student_groups=self.student_repo.get_student_groups(student_id),
            participations=participations,
            task_logs=self.student_repo.get_task_logs(student_id),
            work_group_refs=self.student_repo.get_work_group_refs(work_ids),
        )
