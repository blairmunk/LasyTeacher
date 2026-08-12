"""Read port for student groups/classes."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.student import (
    StudentGroupDetail,
    StudentGroupListItem,
    StudentGroupRef,
)


class IStudentGroupCatalogRepository(ABC):
    @abstractmethod
    def get_list_student_groups(
        self,
        year: AcademicYearRef | None = None,
    ) -> List[StudentGroupListItem]:
        """Return student groups/classes for the group list page."""

    @abstractmethod
    def get_student_group(
        self,
        group_id: str,
    ) -> Optional[StudentGroupDetail]:
        """Return one student group detail read model, or None."""

    @abstractmethod
    def get_all_student_groups(self) -> List[StudentGroupRef]:
        """Return all student groups/classes for selection controls."""

    @abstractmethod
    def get_group_name(self, group_id: str) -> Optional[str]:
        """Return a student group name."""
