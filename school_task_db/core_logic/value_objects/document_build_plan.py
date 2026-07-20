"""Build plan DTOs for section-based documents."""

from dataclasses import dataclass

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
)


@dataclass(frozen=True)
class DocumentSectionPayloadBuildRequest:
    source: DocumentSourceRef
    recipe: DocumentRecipe
    section: DocumentSectionSpec
