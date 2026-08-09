"""Document engine interface."""

from abc import ABC, abstractmethod

from core_logic.entities.document_rendering import (
    GeneratedDocument,
)
from core_logic.value_objects.document_render_plan import DocumentRenderPlan


class IDocumentEngine(ABC):
    @abstractmethod
    def render_document(
        self,
        render_plan: DocumentRenderPlan,
    ) -> GeneratedDocument:
        """Render document files from a generic render plan."""
