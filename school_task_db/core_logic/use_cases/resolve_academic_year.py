"""Resolve the academic year selected for the current request."""

from dataclasses import dataclass

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.interfaces.academic_year_repo import IAcademicYearRepository


@dataclass(frozen=True)
class ResolveAcademicYearRequest:
    requested_year_id: str = ''
    stored_year_id: str = ''


@dataclass(frozen=True)
class AcademicYearSelection:
    current_year: AcademicYearRef | None

    @property
    def year_id(self) -> str:
        return self.current_year.pk if self.current_year else ''


class ResolveAcademicYearUseCase:
    def __init__(self, academic_year_repo: IAcademicYearRepository):
        self.academic_year_repo = academic_year_repo

    def execute(
        self,
        request: ResolveAcademicYearRequest,
    ) -> AcademicYearSelection:
        selected_year = self._get_selected_year(request)
        if selected_year is None:
            selected_year = self.academic_year_repo.get_active_academic_year()
        return AcademicYearSelection(current_year=selected_year)

    def _get_selected_year(
        self,
        request: ResolveAcademicYearRequest,
    ) -> AcademicYearRef | None:
        year_id = request.requested_year_id or request.stored_year_id
        if not year_id:
            return None
        return self.academic_year_repo.get_academic_year(year_id)

