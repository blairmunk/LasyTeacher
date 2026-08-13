"""Read port for one class journal report."""

from abc import ABC, abstractmethod

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.journal import JournalSource


class IJournalReportRepository(ABC):
    @abstractmethod
    def get_journal_source(
        self,
        course_id: str,
        group_id: str,
        year: AcademicYearRef | None,
    ) -> JournalSource:
        """Return normalized facts for the class journal."""
