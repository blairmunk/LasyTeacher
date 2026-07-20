"""Render plan for section-based document generation."""

from collections.abc import Callable
from dataclasses import dataclass

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSection,
    DocumentSourceRef,
    DocumentTemplateSpec,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    RenderTarget,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_recipes import (
    build_remedial_sheet_document_recipe,
    build_work_document_recipe,
)


@dataclass(frozen=True)
class DocumentRenderPlan:
    source: DocumentSourceRef
    recipe: DocumentRecipe
    render_target: RenderTarget


@dataclass(frozen=True)
class DocumentRenderRequest:
    document: Document
    render_target: RenderTarget


@dataclass(frozen=True)
class DocumentSectionRenderRequest:
    document: Document
    section: DocumentSection
    render_target: RenderTarget


@dataclass(frozen=True)
class DocumentContentWrapRequest:
    document: Document
    render_target: RenderTarget
    body_content: str


def build_work_document_render_plan(
    work_id: str,
    work_name: str,
    options: WorkDocumentRenderOptions,
    template_spec: DocumentTemplateSpec | None = None,
) -> DocumentRenderPlan:
    recipe = _recipe_from_template_or_default(
        template_spec=template_spec,
        default_recipe_builder=(
            lambda: build_work_document_recipe(options.build_options)
        ),
    )
    return DocumentRenderPlan(
        source=DocumentSourceRef(
            source_type=WORK_SOURCE_TYPE,
            source_id=work_id,
            title=work_name,
        ),
        recipe=recipe,
        render_target=options.render_target,
    )


def build_remedial_sheet_document_render_plan(
    variant_id: str,
    options: RemedialSheetDocumentRenderOptions,
    template_spec: DocumentTemplateSpec | None = None,
) -> DocumentRenderPlan:
    recipe = _recipe_from_template_or_default(
        template_spec=template_spec,
        default_recipe_builder=(
            lambda: build_remedial_sheet_document_recipe(
                options.build_options,
            )
        ),
    )
    return DocumentRenderPlan(
        source=DocumentSourceRef(
            source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
            source_id=variant_id,
        ),
        recipe=recipe,
        render_target=options.render_target,
    )


def _recipe_from_template_or_default(
    template_spec: DocumentTemplateSpec | None,
    default_recipe_builder: Callable[[], DocumentRecipe],
) -> DocumentRecipe:
    if template_spec:
        return template_spec.to_recipe()
    return default_recipe_builder()
