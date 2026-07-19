"""Render document files for a remedial sheet."""

from dataclasses import dataclass

from core_logic.entities.document_rendering import DocumentRenderResult
from core_logic.interfaces.document_rendering_service import (
    IDocumentRenderingService,
)
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.value_objects.content_config import RemedialSheetDocumentRenderOptions
from core_logic.value_objects.document_render_plan import (
    build_remedial_sheet_document_render_plan,
)


SUPPORTED_REMEDIAL_SHEET_RENDERER_TYPES = {'latex', 'html', 'pdf'}


@dataclass(frozen=True)
class RenderRemedialSheetDocumentRequest:
    variant_id: str
    options: RemedialSheetDocumentRenderOptions


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
                status='not_found',
                renderer_type=request.options.renderer_type,
            )
        if variant_type != 'remedial':
            return DocumentRenderResult(
                status='not_remedial',
                renderer_type=request.options.renderer_type,
            )
        if (
            request.options.renderer_type
            not in SUPPORTED_REMEDIAL_SHEET_RENDERER_TYPES
        ):
            return DocumentRenderResult(
                status='unsupported_generator',
                renderer_type=request.options.renderer_type,
            )

        document = self.document_rendering_service.render_remedial_sheet_document(
            request.variant_id,
            request.options,
            build_remedial_sheet_document_render_plan(
                variant_id=request.variant_id,
                options=request.options,
            ),
        )
        status = 'generated' if document.files else 'empty'
        return DocumentRenderResult(
            status=status,
            renderer_type=request.options.renderer_type,
            file_type=document.file_type,
            files=document.files,
        )
