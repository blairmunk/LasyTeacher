"""Build student group detail screen data."""

from core_logic.entities.student import StudentGroupDetailData
from core_logic.interfaces.student_group_catalog_repo import (
    IStudentGroupCatalogRepository,
)


class GetStudentGroupDetailUseCase:
    def __init__(self, student_repo: IStudentGroupCatalogRepository):
        self.student_repo = student_repo

    def execute(self, group_id: str) -> StudentGroupDetailData:
        return StudentGroupDetailData(
            student_group=self.student_repo.get_student_group(group_id),
        )
