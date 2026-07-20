"""Document engine interface."""

from abc import ABC, abstractmethod

from core_logic.entities.document_rendering import (
    GeneratedDocument,
    GeneratedFileResult,
)
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import DocumentRenderPlan


class IDocumentEngine(ABC):
    @abstractmethod
    def render_work_document(
        self,
        work_id: str,
        options: WorkDocumentRenderOptions,
        render_plan: DocumentRenderPlan | None = None,
    ) -> GeneratedDocument:
        """Render document files for a whole work."""

    @abstractmethod
    def render_remedial_sheet_document(
        self,
        variant_id: str,
        options: RemedialSheetDocumentRenderOptions,
        render_plan: DocumentRenderPlan | None = None,
    ) -> GeneratedDocument:
        """Render document files for a remedial variant."""

    @abstractmethod
    def get_rendered_file(
        self,
        file_type: str,
        filename: str,
    ) -> GeneratedFileResult:
        """Return rendered file contents for downloading."""
