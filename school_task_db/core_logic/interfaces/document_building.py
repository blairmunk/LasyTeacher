"""Interfaces for section-based document building."""

from abc import ABC, abstractmethod
from typing import Any, Mapping

from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)


class IDocumentSectionPayloadBuilder(ABC):
    @abstractmethod
    def build_payload(
        self,
        request: DocumentSectionPayloadBuildRequest,
    ) -> Mapping[str, Any]:
        """Build data payload for one document section."""
