"""Interfaces for section-based document building."""

from abc import ABC, abstractmethod
from typing import Any, Mapping

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSourceRef,
)
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)


class IDocumentBuilder(ABC):
    @abstractmethod
    def build(
        self,
        source: DocumentSourceRef,
        recipe: DocumentRecipe,
        render_target: RenderTarget | None = None,
    ) -> Document:
        """Build a generic document from a source and a section recipe."""


class IDocumentSectionPayloadBuilder(ABC):
    @abstractmethod
    def build_payload(
        self,
        request: DocumentSectionPayloadBuildRequest,
    ) -> Mapping[str, Any]:
        """Build data payload for one document section."""
