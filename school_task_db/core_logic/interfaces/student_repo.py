"""Student repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.student import (
    SaveStudentGroupParams,
    SaveStudentGroupResult,
    SaveStudentParams,
    SaveStudentResult,
    StudentDetail,
    StudentListItem,
    StudentGroupDetail,
    StudentGroupListItem,
    StudentGroupRef,
)


class IStudentRepository(ABC):
    @abstractmethod
    def get_list_students(
        self,
        year: AcademicYearRef | None = None,
    ) -> List[StudentListItem]:
        """Return students for the student list page."""

    @abstractmethod
    def get_list_student_groups(
        self,
        year: AcademicYearRef | None = None,
    ) -> List[StudentGroupListItem]:
        """Return student groups/classes for the group list page."""

    @abstractmethod
    def get_student(self, student_id: str) -> Optional[StudentDetail]:
        """Return one student detail read model, or None."""

    @abstractmethod
    def get_student_group(self, group_id: str) -> Optional[StudentGroupDetail]:
        """Return one student group detail read model, or None."""

    @abstractmethod
    def create_student(self, params: SaveStudentParams) -> SaveStudentResult:
        """Create a student."""

    @abstractmethod
    def update_student(self, params: SaveStudentParams) -> SaveStudentResult:
        """Update a student, or return not_found status."""

    @abstractmethod
    def create_student_group(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        """Create a student group/class."""

    @abstractmethod
    def update_student_group(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        """Update a student group/class, or return not_found status."""

    @abstractmethod
    def get_student_groups(self, student_id: str) -> List[StudentGroupRef]:
        """Return groups/classes containing the student."""

    @abstractmethod
    def get_all_student_groups(self) -> List[StudentGroupRef]:
        """Return all student groups/classes for selection controls."""

    @abstractmethod
    def get_group_name(self, group_id: str) -> Optional[str]:
        """Return a student group name."""
