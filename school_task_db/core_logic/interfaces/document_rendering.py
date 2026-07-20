"""Interfaces for section-based document rendering."""

from abc import ABC, abstractmethod

from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.value_objects.document_render_plan import (
    DocumentContentWrapRequest,
    DocumentRenderRequest,
    DocumentSectionRenderRequest,
)


class IDocumentRenderer(ABC):
    @abstractmethod
    def render(
        self,
        request: DocumentRenderRequest,
    ) -> GeneratedDocument:
        """Render a generic document to files for the selected target."""


class IDocumentSectionRenderer(ABC):
    @abstractmethod
    def render_section(
        self,
        request: DocumentSectionRenderRequest,
    ) -> str:
        """Render one document section for the selected target."""


class IDocumentContentWrapper(ABC):
    @abstractmethod
    def wrap_content(
        self,
        request: DocumentContentWrapRequest,
    ) -> str:
        """Wrap rendered section body into a complete document."""
