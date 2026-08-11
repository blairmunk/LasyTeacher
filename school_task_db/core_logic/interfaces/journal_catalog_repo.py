"""Read port for available class journals."""

from abc import ABC, abstractmethod

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.journal import JournalSelectData


class IJournalCatalogRepository(ABC):
    @abstractmethod
    def get_journal_select(
        self,
        year: AcademicYearRef | None,
    ) -> JournalSelectData:
        """Return course-group pairs available for journal view."""
