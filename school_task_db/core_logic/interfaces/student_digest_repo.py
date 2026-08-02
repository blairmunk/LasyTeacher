"""Read boundary for student grade digests."""

from abc import ABC, abstractmethod
from datetime import date

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.student_digest import (
    StudentDigestGroupRef,
    StudentDigestSource,
)


class IStudentDigestRepository(ABC):
    @abstractmethod
    def get_digest_groups(
        self,
        year: AcademicYearRef | None,
    ) -> tuple[StudentDigestGroupRef, ...]:
        """Return groups available for digest generation."""

    @abstractmethod
    def get_student_digest_source(
        self,
        group_id: str,
        start_date: date,
        end_date: date,
    ) -> StudentDigestSource | None:
        """Return normalized grade facts for one group and period."""
