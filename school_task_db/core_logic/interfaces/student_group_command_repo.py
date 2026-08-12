"""Command port for student groups/classes."""

from abc import ABC, abstractmethod

from core_logic.entities.student import (
    SaveStudentGroupParams,
    SaveStudentGroupResult,
)


class IStudentGroupCommandRepository(ABC):
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
