"""Build student group list screen data."""

from core_logic.entities.student import StudentGroupListData
from core_logic.interfaces.student_repo import IStudentRepository


class GetStudentGroupListUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(self) -> StudentGroupListData:
        return StudentGroupListData(
            student_groups=self.student_repo.get_list_student_groups(),
        )
