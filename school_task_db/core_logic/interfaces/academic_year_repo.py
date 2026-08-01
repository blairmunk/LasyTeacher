"""Academic year repository interface."""

from abc import ABC, abstractmethod

from core_logic.entities.academic_year import AcademicYearRef


class IAcademicYearRepository(ABC):
    @abstractmethod
    def get_academic_year(self, year_id: str) -> AcademicYearRef | None:
        """Return one academic year or None."""

    @abstractmethod
    def get_active_academic_year(self) -> AcademicYearRef | None:
        """Return the globally active academic year or None."""

    @abstractmethod
    def get_academic_years(self) -> list[AcademicYearRef]:
        """Return all academic years in display order."""

    @abstractmethod
    def activate_academic_year(
        self,
        year_id: str,
    ) -> AcademicYearRef | None:
        """Make one academic year globally active and return it."""
