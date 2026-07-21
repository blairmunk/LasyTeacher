"""Build student list screen data."""

from core_logic.entities.student import StudentListData
from core_logic.interfaces.student_repo import IStudentRepository


class GetStudentListUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(self, year=None) -> StudentListData:
        return StudentListData(
            students=self.student_repo.get_list_students(year=year),
        )
