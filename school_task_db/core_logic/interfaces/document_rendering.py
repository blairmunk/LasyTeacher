"""Interfaces for section-based document rendering."""

from abc import ABC, abstractmethod

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSourceRef,
)
from core_logic.entities.document_generation import GeneratedDocument
from core_logic.value_objects.content_config import RenderTarget


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
        document: Document,
        render_target: RenderTarget,
    ) -> GeneratedDocument:
        """Render a generic document to files for the selected target."""
