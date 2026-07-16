"""Build student detail screen data."""

from core_logic.interfaces.student_repo import IStudentRepository


class GetStudentDetailUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def get_queryset(self):
        return self.student_repo.get_detail_students()
