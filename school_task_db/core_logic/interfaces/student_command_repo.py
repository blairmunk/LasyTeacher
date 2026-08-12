"""Command port for student records."""

from abc import ABC, abstractmethod

from core_logic.entities.student import SaveStudentParams, SaveStudentResult


class IStudentCommandRepository(ABC):
    @abstractmethod
    def create_student(self, params: SaveStudentParams) -> SaveStudentResult:
        """Create a student."""

    @abstractmethod
    def update_student(self, params: SaveStudentParams) -> SaveStudentResult:
        """Update a student, or return not_found status."""
