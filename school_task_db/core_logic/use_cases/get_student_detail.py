"""Build student detail screen data."""

from core_logic.entities.student import StudentDetailData
from core_logic.interfaces.student_catalog_repo import IStudentCatalogRepository


class GetStudentDetailUseCase:
    def __init__(self, student_repo: IStudentCatalogRepository):
        self.student_repo = student_repo

    def execute(self, student_id: str) -> StudentDetailData:
        return StudentDetailData(
            student=self.student_repo.get_student(student_id),
        )
