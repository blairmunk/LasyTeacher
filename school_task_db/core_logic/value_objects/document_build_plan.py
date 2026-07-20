"""Build plan DTOs for section-based documents."""

from dataclasses import dataclass

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
)
from core_logic.value_objects.content_config import RenderTarget


@dataclass(frozen=True)
class DocumentSectionPayloadBuildRequest:
    source: DocumentSourceRef
    recipe: DocumentRecipe
    section: DocumentSectionSpec
    render_target: RenderTarget | None = None
