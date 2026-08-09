"""Render a sectioned document from an explicit document recipe."""

from dataclasses import dataclass

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSourceRef,
)
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.value_objects.document_render_options import (
    RenderTarget,
    is_supported_document_renderer_type,
)
from core_logic.value_objects.document_render_plan import DocumentRenderPlan


@dataclass(frozen=True)
class RenderDocumentFromRecipeRequest:
    source: DocumentSourceRef
    recipe: DocumentRecipe
    render_target: RenderTarget
    source_name: str = ''
    empty_status: str = DOCUMENT_RENDER_STATUS_GENERATED


class RenderDocumentFromRecipeUseCase:
    def __init__(
        self,
        document_engine: IDocumentEngine | None = None,
    ):
        if document_engine is None:
            raise ValueError('Document engine dependency is required.')
        self.document_engine = document_engine

    def execute(
        self,
        request: RenderDocumentFromRecipeRequest,
    ) -> DocumentRenderResult:
        renderer_type = request.render_target.renderer_type
        source_name = request.source_name or request.source.title
        if not is_supported_document_renderer_type(renderer_type):
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
                renderer_type=renderer_type,
                source_name=source_name,
            )

        render_plan = DocumentRenderPlan(
            source=request.source,
            recipe=request.recipe,
            render_target=request.render_target,
        )
        document = self.document_engine.render_document(render_plan)
        status = (
            DOCUMENT_RENDER_STATUS_GENERATED
            if document.files
            else request.empty_status
        )
        return DocumentRenderResult(
            status=status,
            renderer_type=renderer_type,
            file_type=document.file_type,
            files=document.files,
            source_name=source_name,
        )
