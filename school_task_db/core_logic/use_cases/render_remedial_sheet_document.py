"""Render document files for a remedial sheet."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    DocumentRenderResult,
)
from core_logic.interfaces.document_rendering_service import (
    IDocumentRenderingService,
)
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    SUPPORTED_DOCUMENT_RENDERER_TYPES,
)
from core_logic.value_objects.document_render_plan import (
    build_remedial_sheet_document_render_plan,
)


SUPPORTED_REMEDIAL_SHEET_RENDERER_TYPES = SUPPORTED_DOCUMENT_RENDERER_TYPES


@dataclass(frozen=True)
class RenderRemedialSheetDocumentRequest:
    variant_id: str
    options: RemedialSheetDocumentRenderOptions
    template_spec: DocumentTemplateSpec | None = None


class RenderRemedialSheetDocumentUseCase:
    def __init__(
        self,
        document_rendering_service: IDocumentRenderingService | None = None,
        work_repo: IWorkRepository | None = None,
        document_generation_service: IDocumentRenderingService | None = None,
    ):
        self.document_rendering_service = (
            document_rendering_service or document_generation_service
        )
        self.work_repo = work_repo

    def execute(
        self,
        request: RenderRemedialSheetDocumentRequest,
    ) -> DocumentRenderResult:
        variant_type = self.work_repo.get_variant_type(request.variant_id)
        if variant_type is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=request.options.renderer_type,
            )
        if variant_type != 'remedial':
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
                renderer_type=request.options.renderer_type,
            )
        if (
            request.options.renderer_type
            not in SUPPORTED_REMEDIAL_SHEET_RENDERER_TYPES
        ):
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
                renderer_type=request.options.renderer_type,
            )

        document = self.document_rendering_service.render_remedial_sheet_document(
            request.variant_id,
            request.options,
            build_remedial_sheet_document_render_plan(
                variant_id=request.variant_id,
                options=request.options,
                template_spec=request.template_spec,
            ),
        )
        status = (
            DOCUMENT_RENDER_STATUS_GENERATED
            if document.files
            else DOCUMENT_RENDER_STATUS_EMPTY
        )
        return DocumentRenderResult(
            status=status,
            renderer_type=request.options.renderer_type,
            file_type=document.file_type,
            files=document.files,
        )
