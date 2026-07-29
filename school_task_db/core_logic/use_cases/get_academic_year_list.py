"""List academic years available to the presentation layer."""

from dataclasses import dataclass

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.interfaces.academic_year_repo import IAcademicYearRepository


@dataclass(frozen=True)
class AcademicYearListData:
    academic_years: list[AcademicYearRef]


class GetAcademicYearListUseCase:
    def __init__(self, academic_year_repo: IAcademicYearRepository):
        self.academic_year_repo = academic_year_repo

    def execute(self) -> AcademicYearListData:
        return AcademicYearListData(
            academic_years=self.academic_year_repo.get_academic_years(),
        )

