"""Render document files for a work."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    DocumentRenderResult,
)
from core_logic.interfaces.document_rendering_service import (
    IDocumentRenderingService,
)
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.value_objects.content_config import (
    SUPPORTED_DOCUMENT_RENDERER_TYPES,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import (
    build_work_document_render_plan,
)
from core_logic.value_objects.document_recipes import WORK_DOCUMENT_TYPE


SUPPORTED_WORK_RENDERER_TYPES = SUPPORTED_DOCUMENT_RENDERER_TYPES


@dataclass(frozen=True)
class RenderWorkDocumentRequest:
    work_id: str
    options: WorkDocumentRenderOptions
    template_spec: DocumentTemplateSpec | None = None


class RenderWorkDocumentUseCase:
    def __init__(
        self,
        document_rendering_service: IDocumentRenderingService | None = None,
        work_repo: IWorkRepository | None = None,
        document_template_repo: IDocumentTemplateRepository | None = None,
        document_generation_service: IDocumentRenderingService | None = None,
    ):
        self.document_rendering_service = (
            document_rendering_service or document_generation_service
        )
        self.work_repo = work_repo
        self.document_template_repo = document_template_repo

    def execute(
        self,
        request: RenderWorkDocumentRequest,
    ) -> DocumentRenderResult:
        renderer_type = request.options.renderer_type
        work_name = self.work_repo.get_work_name(request.work_id)
        if work_name is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=renderer_type,
            )

        if renderer_type not in SUPPORTED_WORK_RENDERER_TYPES:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
                renderer_type=renderer_type,
                source_name=work_name,
            )

        document = self.document_rendering_service.render_work_document(
            request.work_id,
            request.options,
            build_work_document_render_plan(
                work_id=request.work_id,
                work_name=work_name,
                options=request.options,
                template_spec=(
                    request.template_spec
                    or self._default_template_spec()
                ),
            ),
        )
        return DocumentRenderResult(
            status=DOCUMENT_RENDER_STATUS_GENERATED,
            renderer_type=renderer_type,
            file_type=document.file_type,
            files=document.files,
            source_name=work_name,
        )

    def _default_template_spec(self):
        if self.document_template_repo is None:
            return None
        return self.document_template_repo.get_default_template_spec(
            WORK_DOCUMENT_TYPE,
        )
