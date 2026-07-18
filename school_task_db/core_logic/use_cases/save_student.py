"""Create and update students and student groups."""

from core_logic.entities.student import (
    SaveStudentGroupParams,
    SaveStudentGroupResult,
    SaveStudentParams,
    SaveStudentResult,
)
from core_logic.interfaces.student_repo import IStudentRepository


class CreateStudentUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(self, params: SaveStudentParams) -> SaveStudentResult:
        return self.student_repo.create_student(params)


class UpdateStudentUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(self, params: SaveStudentParams) -> SaveStudentResult:
        return self.student_repo.update_student(params)


class CreateStudentGroupUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        return self.student_repo.create_student_group(params)


class UpdateStudentGroupUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        return self.student_repo.update_student_group(params)
