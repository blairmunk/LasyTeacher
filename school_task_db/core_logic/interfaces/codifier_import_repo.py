"""Command persistence port for codifier imports."""

from abc import ABC, abstractmethod

from core_logic.entities.codifier_import import CodifierImportDefinition


class ICodifierImportRepository(ABC):
    @abstractmethod
    def codifier_exists(
        self,
        exam_type: str,
        year: int,
        subject: str,
    ) -> bool:
        """Return whether the codifier identity already exists."""

    @abstractmethod
    def delete_codifier(
        self,
        exam_type: str,
        year: int,
        subject: str,
    ) -> int:
        """Delete the codifier and return the cascaded object count."""

    @abstractmethod
    def create_codifier(self, definition: CodifierImportDefinition) -> str:
        """Persist a validated codifier and return its display name."""
