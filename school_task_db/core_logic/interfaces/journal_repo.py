"""Port for class journal report data."""

from abc import ABC, abstractmethod
from typing import Any

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.journal import JournalSelectData, JournalSource


class IJournalRepository(ABC):
    @abstractmethod
    def get_journal_select(
        self,
        year: AcademicYearRef | None,
    ) -> JournalSelectData:
        """Return course-group pairs available for journal view."""

    @abstractmethod
    def get_journal_source(
        self,
        course_id: Any,
        group_id: Any,
        year: AcademicYearRef | None,
    ) -> JournalSource:
        """Return normalized facts for the class journal."""
