"""Build data for a student's remedial work page."""

from core_logic.entities.student import StudentRemedialWorkData
from core_logic.interfaces.student_repo import IStudentRepository


class GetStudentRemedialWorkUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(self, student_id: str) -> StudentRemedialWorkData:
        return self.student_repo.get_student_remedial_work_data(student_id)
