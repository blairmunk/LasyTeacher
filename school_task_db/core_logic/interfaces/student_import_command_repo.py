"""Command port for applying a planned student import."""

from abc import ABC, abstractmethod

from core_logic.entities.student_import import StudentImportPlan


class IStudentImportCommandRepository(ABC):
    @abstractmethod
    def apply_student_import_plan(self, plan: StudentImportPlan) -> None:
        """Apply a validated student import plan."""
