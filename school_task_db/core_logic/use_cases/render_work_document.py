"""Render document files for a work."""

from dataclasses import dataclass

from core_logic.entities.document_generation import DocumentGenerationResult
from core_logic.interfaces.document_generation import IDocumentGenerationService
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.value_objects.content_config import WorkDocumentRenderOptions
from core_logic.value_objects.document_render_plan import (
    build_work_document_render_plan,
)


SUPPORTED_WORK_RENDERER_TYPES = {'latex', 'html', 'pdf'}


@dataclass(frozen=True)
class RenderWorkDocumentRequest:
    work_id: str
    options: WorkDocumentRenderOptions


class RenderWorkDocumentUseCase:
    def __init__(
        self,
        document_generation_service: IDocumentGenerationService,
        work_repo: IWorkRepository,
    ):
        self.document_generation_service = document_generation_service
        self.work_repo = work_repo

    def execute(
        self,
        request: RenderWorkDocumentRequest,
    ) -> DocumentGenerationResult:
        renderer_type = request.options.renderer_type
        work_name = self.work_repo.get_work_name(request.work_id)
        if work_name is None:
            return DocumentGenerationResult(
                status='not_found',
                renderer_type=renderer_type,
            )

        if renderer_type not in SUPPORTED_WORK_RENDERER_TYPES:
            return DocumentGenerationResult(
                status='unsupported_generator',
                renderer_type=renderer_type,
                source_name=work_name,
            )

        document = self.document_generation_service.render_work_document(
            request.work_id,
            request.options,
            build_work_document_render_plan(
                work_id=request.work_id,
                work_name=work_name,
                options=request.options,
            ),
        )
        return DocumentGenerationResult(
            status='generated',
            renderer_type=renderer_type,
            file_type=document.file_type,
            files=document.files,
            source_name=work_name,
        )
