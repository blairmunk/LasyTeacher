"""Render document files from a generic render plan."""

from dataclasses import dataclass

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.use_cases.document_engine_dependency import resolve_document_engine
from core_logic.value_objects.document_render_options import (
    is_supported_document_renderer_type,
)
from core_logic.value_objects.document_render_plan import DocumentRenderPlan


@dataclass(frozen=True)
class RenderDocumentRequest:
    render_plan: DocumentRenderPlan
    source_name: str = ''
    empty_status: str = DOCUMENT_RENDER_STATUS_GENERATED


class RenderDocumentUseCase:
    def __init__(
        self,
        document_engine: IDocumentEngine | None = None,
    ):
        self.document_engine = resolve_document_engine(
            document_engine=document_engine,
        )

    def execute(
        self,
        request: RenderDocumentRequest,
    ) -> DocumentRenderResult:
        renderer_type = request.render_plan.render_target.renderer_type
        if not is_supported_document_renderer_type(renderer_type):
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
                renderer_type=renderer_type,
                source_name=request.source_name,
            )

        document = self.document_engine.render_document(request.render_plan)
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
            source_name=request.source_name,
        )
