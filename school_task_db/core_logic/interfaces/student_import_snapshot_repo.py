"""Read-only port for planning a student import."""

from abc import ABC, abstractmethod

from core_logic.entities.student_import import StudentImportSnapshot


class IStudentImportSnapshotRepository(ABC):
    @abstractmethod
    def get_student_import_snapshot(self) -> StudentImportSnapshot:
        """Return current years, groups, students and memberships."""
