"""Build student group list screen data."""

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.student import StudentGroupListData
from core_logic.interfaces.student_group_catalog_repo import (
    IStudentGroupCatalogRepository,
)


class GetStudentGroupListUseCase:
    def __init__(self, student_repo: IStudentGroupCatalogRepository):
        self.student_repo = student_repo

    def execute(
        self,
        year: AcademicYearRef | None = None,
    ) -> StudentGroupListData:
        return StudentGroupListData(
            student_groups=self.student_repo.get_list_student_groups(year=year),
        )
