"""Render a sectioned document from explicit print settings."""

from dataclasses import dataclass

from core_logic.entities.document import (
    DocumentSourceRef,
    PrintSettingsSpec,
)
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeRequest,
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import RenderTarget


@dataclass(frozen=True)
class RenderDocumentFromPrintSettingsRequest:
    source: DocumentSourceRef
    render_target: RenderTarget
    print_settings_spec: PrintSettingsSpec
    source_name: str = ''
    empty_status: str = DOCUMENT_RENDER_STATUS_GENERATED


class RenderDocumentFromPrintSettingsUseCase:
    """Render a sectioned document from print settings."""

    def __init__(
        self,
        document_engine: IDocumentEngine | None = None,
        render_document_from_recipe_use_case: (
            RenderDocumentFromRecipeUseCase | None
        ) = None,
    ):
        self.render_document_from_recipe_use_case = (
            render_document_from_recipe_use_case
            or RenderDocumentFromRecipeUseCase(document_engine=document_engine)
        )

    def execute(
        self,
        request: RenderDocumentFromPrintSettingsRequest,
    ) -> DocumentRenderResult:
        return self.render_document_from_recipe_use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=request.source,
                recipe=request.print_settings_spec.to_print_recipe(),
                render_target=request.render_target,
                source_name=request.source_name or request.source.title,
                empty_status=request.empty_status,
            )
        )
