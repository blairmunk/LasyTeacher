"""Build plan DTOs for section-based documents."""

from dataclasses import dataclass, field
from typing import Any, MutableMapping

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
)
from core_logic.value_objects.document_render_options import RenderTarget


@dataclass(frozen=True)
class DocumentSectionPayloadBuildRequest:
    source: DocumentSourceRef
    recipe: DocumentRecipe
    section: DocumentSectionSpec
    render_target: RenderTarget | None = None
    build_context: MutableMapping[str, Any] = field(default_factory=dict)
