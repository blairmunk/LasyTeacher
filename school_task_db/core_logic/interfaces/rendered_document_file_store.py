"""Port for reading files produced by the document engine."""

from abc import ABC, abstractmethod

from core_logic.entities.document_rendering import GeneratedFileResult


class IRenderedDocumentFileStore(ABC):
    @abstractmethod
    def get_file(
        self,
        file_type: str,
        filename: str,
    ) -> GeneratedFileResult:
        """Return one rendered file for download."""
