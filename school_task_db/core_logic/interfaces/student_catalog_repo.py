"""Read port for student catalog and detail data."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.student import (
    StudentDetail,
    StudentGroupRef,
    StudentListItem,
)


class IStudentCatalogRepository(ABC):
    @abstractmethod
    def get_list_students(
        self,
        year: AcademicYearRef | None = None,
    ) -> List[StudentListItem]:
        """Return students for the student list page."""

    @abstractmethod
    def get_student(self, student_id: str) -> Optional[StudentDetail]:
        """Return one student detail read model, or None."""

    @abstractmethod
    def get_student_groups(self, student_id: str) -> List[StudentGroupRef]:
        """Return groups/classes containing the student."""
