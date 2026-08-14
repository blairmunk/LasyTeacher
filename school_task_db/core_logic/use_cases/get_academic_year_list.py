"""List academic years available to the presentation layer."""

from dataclasses import dataclass

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.interfaces.academic_year_catalog_repo import (
    IAcademicYearCatalogRepository,
)


@dataclass(frozen=True)
class AcademicYearListData:
    academic_years: tuple[AcademicYearRef, ...]

    def __post_init__(self):
        object.__setattr__(
            self,
            'academic_years',
            tuple(self.academic_years),
        )


class GetAcademicYearListUseCase:
    def __init__(self, academic_year_repo: IAcademicYearCatalogRepository):
        self.academic_year_repo = academic_year_repo

    def execute(self) -> AcademicYearListData:
        return AcademicYearListData(
            academic_years=self.academic_year_repo.get_academic_years(),
        )
