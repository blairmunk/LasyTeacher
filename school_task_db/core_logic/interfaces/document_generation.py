"""Document generation service interface."""

from abc import ABC, abstractmethod

from core_logic.entities.document_generation import (
    GeneratedDocument,
    GeneratedFileResult,
)
from core_logic.value_objects.content_config import (
    RemedialSheetGenerationOptions,
    WorkGenerationOptions,
)


class IDocumentGenerationService(ABC):
    @abstractmethod
    def render_work_document(
        self,
        work_id: str,
        options: WorkGenerationOptions,
    ) -> GeneratedDocument:
        """Render document files for a whole work."""

    @abstractmethod
    def render_remedial_sheet_document(
        self,
        variant_id: str,
        options: RemedialSheetGenerationOptions,
    ) -> GeneratedDocument:
        """Render document files for a remedial variant."""

    def generate_work(
        self,
        work_id: str,
        options: WorkGenerationOptions,
    ) -> GeneratedDocument:
        """Backward-compatible alias for render_work_document."""
        return self.render_work_document(work_id, options)

    def generate_remedial_sheet(
        self,
        variant_id: str,
        options: RemedialSheetGenerationOptions,
    ) -> GeneratedDocument:
        """Backward-compatible alias for render_remedial_sheet_document."""
        return self.render_remedial_sheet_document(variant_id, options)

    @abstractmethod
    def get_generated_file(
        self,
        file_type: str,
        filename: str,
    ) -> GeneratedFileResult:
        """Return generated file contents for downloading."""
