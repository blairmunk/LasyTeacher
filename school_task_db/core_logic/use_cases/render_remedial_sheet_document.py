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
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.use_cases.document_engine_dependency import resolve_document_engine
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    SUPPORTED_DOCUMENT_RENDERER_TYPES,
)
from core_logic.value_objects.document_render_plan import (
    build_remedial_sheet_document_render_plan,
)
from core_logic.value_objects.document_recipes import REMEDIAL_SHEET_DOCUMENT_TYPE


SUPPORTED_REMEDIAL_SHEET_RENDERER_TYPES = SUPPORTED_DOCUMENT_RENDERER_TYPES


@dataclass(frozen=True)
class RenderRemedialSheetDocumentRequest:
    variant_id: str
    options: RemedialSheetDocumentRenderOptions
    template_spec: DocumentTemplateSpec | None = None


class RenderRemedialSheetDocumentUseCase:
    def __init__(
        self,
        document_rendering_service: IDocumentEngine | None = None,
        work_repo: IWorkRepository | None = None,
        document_template_repo: IDocumentTemplateRepository | None = None,
        document_generation_service: IDocumentEngine | None = None,
        document_engine: IDocumentEngine | None = None,
    ):
        self.document_engine = resolve_document_engine(
            document_engine=document_engine,
            document_rendering_service=document_rendering_service,
            document_generation_service=document_generation_service,
        )
        self.work_repo = work_repo
        self.document_template_repo = document_template_repo

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

        document = self.document_engine.render_remedial_sheet_document(
            request.variant_id,
            request.options,
            build_remedial_sheet_document_render_plan(
                variant_id=request.variant_id,
                options=request.options,
                template_spec=(
                    request.template_spec
                    or self._default_template_spec()
                ),
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

    def _default_template_spec(self):
        if self.document_template_repo is None:
            return None
        return self.document_template_repo.get_default_template_spec(
            REMEDIAL_SHEET_DOCUMENT_TYPE,
        )
