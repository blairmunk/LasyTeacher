"""Build data for a student's remedial work page."""

from core_logic.entities.student import StudentRemedialWorkData
from core_logic.interfaces.student_repo import IStudentRepository
from core_logic.services.student_remedial_service import StudentRemedialService


class GetStudentRemedialWorkUseCase:
    def __init__(
        self,
        student_repo: IStudentRepository,
        service: StudentRemedialService | None = None,
    ):
        self.student_repo = student_repo
        self.service = service or StudentRemedialService()

    def execute(self, student_id: str) -> StudentRemedialWorkData:
        return self.service.analyze(
            self.student_repo.get_student_remedial_source(student_id),
        )
