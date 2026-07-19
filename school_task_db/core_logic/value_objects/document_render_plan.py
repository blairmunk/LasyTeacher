"""Render plan for section-based document generation."""

from dataclasses import dataclass

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSourceRef,
)
from core_logic.value_objects.content_config import RenderTarget


@dataclass(frozen=True)
class DocumentRenderPlan:
    source: DocumentSourceRef
    recipe: DocumentRecipe
    render_target: RenderTarget


@dataclass(frozen=True)
class DocumentRenderRequest:
    document: Document
    render_target: RenderTarget
