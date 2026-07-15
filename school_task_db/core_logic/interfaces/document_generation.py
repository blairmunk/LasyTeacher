"""Document generation service interface."""

from abc import ABC, abstractmethod

from core_logic.entities.document_generation import GeneratedDocument
from core_logic.value_objects.content_config import (
    RemedialSheetGenerationOptions,
    WorkGenerationOptions,
)


class IDocumentGenerationService(ABC):
    @abstractmethod
    def generate_work(
        self,
        work_id: str,
        options: WorkGenerationOptions,
    ) -> GeneratedDocument:
        """Generate files for a whole work."""

    @abstractmethod
    def generate_remedial_sheet(
        self,
        variant_id: str,
        options: RemedialSheetGenerationOptions,
    ) -> GeneratedDocument:
        """Generate files for a remedial variant."""
