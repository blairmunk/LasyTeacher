"""Activate one global academic year."""

from dataclasses import dataclass

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.interfaces.academic_year_repo import IAcademicYearRepository


@dataclass(frozen=True)
class ActivateAcademicYearRequest:
    year_id: str


class ActivateAcademicYearUseCase:
    def __init__(self, academic_year_repo: IAcademicYearRepository):
        self.academic_year_repo = academic_year_repo

    def execute(
        self,
        request: ActivateAcademicYearRequest,
    ) -> AcademicYearRef | None:
        if not request.year_id:
            return None
        return self.academic_year_repo.activate_academic_year(request.year_id)
