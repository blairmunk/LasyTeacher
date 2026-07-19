"""Interfaces for section-based document rendering."""

from abc import ABC, abstractmethod

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSourceRef,
)
from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.value_objects.document_render_plan import DocumentRenderRequest


class IDocumentBuilder(ABC):
    @abstractmethod
    def build(
        self,
        source: DocumentSourceRef,
        recipe: DocumentRecipe,
    ) -> Document:
        """Build a generic document from a source and a section recipe."""


class IDocumentRenderer(ABC):
    @abstractmethod
    def render(
        self,
        request: DocumentRenderRequest,
    ) -> GeneratedDocument:
        """Render a generic document to files for the selected target."""
