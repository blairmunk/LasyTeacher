"""Command repository port for academic year activation."""

from abc import ABC, abstractmethod

from core_logic.entities.academic_year import AcademicYearRef


class IAcademicYearActivationRepository(ABC):
    @abstractmethod
    def activate_academic_year(
        self,
        year_id: str,
    ) -> AcademicYearRef | None:
        """Make one academic year globally active and return it."""
