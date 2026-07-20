"""Render a sectioned document from an explicit document recipe."""

from dataclasses import dataclass

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSourceRef,
)
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.use_cases.render_document import (
    RenderDocumentRequest,
    RenderDocumentUseCase,
)
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_plan import (
    build_document_render_plan,
)


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
        render_document_use_case: RenderDocumentUseCase | None = None,
    ):
        self.render_document_use_case = (
            render_document_use_case
            or RenderDocumentUseCase(document_engine=document_engine)
        )

    def execute(
        self,
        request: RenderDocumentFromRecipeRequest,
    ) -> DocumentRenderResult:
        render_plan = build_document_render_plan(
            source=request.source,
            recipe=request.recipe,
            render_target=request.render_target,
        )
        return self.render_document_use_case.execute(
            RenderDocumentRequest(
                render_plan=render_plan,
                source_name=request.source_name or request.source.title,
                empty_status=request.empty_status,
            )
        )
