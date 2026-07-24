"""Legacy adapter for rendering from document print settings."""

from core_logic.entities.document import (
    DocumentSourceRef,
    PrintSettingsSpec,
)
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.use_cases.render_document_from_print_settings import (
    RenderDocumentFromPrintSettingsRequest,
    RenderDocumentFromPrintSettingsUseCase,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import RenderTarget


class RenderDocumentFromTemplateRequest(
    RenderDocumentFromPrintSettingsRequest,
):
    """Adapt the former template-oriented render request."""

    def __init__(
        self,
        source: DocumentSourceRef,
        render_target: RenderTarget,
        template_spec: PrintSettingsSpec | None = None,
        print_settings_spec: PrintSettingsSpec | None = None,
        source_name: str = '',
        empty_status: str = DOCUMENT_RENDER_STATUS_GENERATED,
    ):
        super().__init__(
            source=source,
            render_target=render_target,
            print_settings_spec=print_settings_spec or template_spec,
            source_name=source_name,
            empty_status=empty_status,
        )


class RenderDocumentFromTemplateUseCase(
    RenderDocumentFromPrintSettingsUseCase,
):
    """Adapt the former template-oriented render use case."""

    def __init__(
        self,
        document_engine: IDocumentEngine | None = None,
        render_document_from_recipe_use_case: (
            RenderDocumentFromRecipeUseCase | None
        ) = None,
    ):
        super().__init__(
            document_engine=document_engine,
            render_document_from_recipe_use_case=(
                render_document_from_recipe_use_case
            ),
        )

    def execute(
        self,
        request: RenderDocumentFromTemplateRequest,
    ) -> DocumentRenderResult:
        if request.print_settings_spec is None:
            raise ValueError('print_settings_spec is required')
        return super().execute(request)
