"""Document generation service interface."""

from abc import ABC, abstractmethod
from typing import Any

from core_logic.entities.document_generation import GeneratedDocument
from core_logic.value_objects.content_config import (
    RemedialSheetGenerationOptions,
    WorkGenerationOptions,
)


class IDocumentGenerationService(ABC):
    @abstractmethod
    def generate_work(
        self,
        work: Any,
        options: WorkGenerationOptions,
    ) -> GeneratedDocument:
        """Generate files for a whole work."""

    @abstractmethod
    def generate_remedial_sheet(
        self,
        variant: Any,
        options: RemedialSheetGenerationOptions,
    ) -> GeneratedDocument:
        """Generate files for a remedial variant."""
