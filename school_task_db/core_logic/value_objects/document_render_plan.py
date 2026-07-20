"""Render plan for section-based document generation."""

from dataclasses import dataclass

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSourceRef,
)
from core_logic.value_objects.document_render_options import RenderTarget


@dataclass(frozen=True)
class DocumentRenderPlan:
    source: DocumentSourceRef
    recipe: DocumentRecipe
    render_target: RenderTarget


def build_document_render_plan(
    source: DocumentSourceRef,
    recipe: DocumentRecipe,
    render_target: RenderTarget,
) -> DocumentRenderPlan:
    return DocumentRenderPlan(
        source=source,
        recipe=recipe,
        render_target=render_target,
    )
