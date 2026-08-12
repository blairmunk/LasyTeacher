"""Build student list screen data."""

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.student import StudentListData
from core_logic.interfaces.student_catalog_repo import IStudentCatalogRepository


class GetStudentListUseCase:
    def __init__(self, student_repo: IStudentCatalogRepository):
        self.student_repo = student_repo

    def execute(
        self,
        year: AcademicYearRef | None = None,
    ) -> StudentListData:
        return StudentListData(
            students=self.student_repo.get_list_students(year=year),
        )
