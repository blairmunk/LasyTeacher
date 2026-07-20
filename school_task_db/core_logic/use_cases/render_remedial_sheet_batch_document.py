"""Render remedial sheet documents for all remedial variants in a work."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
    GeneratedDocumentFile,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
)


@dataclass(frozen=True)
class RenderRemedialSheetBatchDocumentRequest:
    work_id: str
    options: RemedialSheetDocumentRenderOptions
    template_spec: DocumentTemplateSpec | None = None


class RenderRemedialSheetBatchDocumentUseCase:
    def __init__(
        self,
        work_repo: IWorkRepository,
        document_template_repo: IDocumentTemplateRepository | None = None,
        document_engine: IDocumentEngine | None = None,
        render_remedial_sheet_document_use_case: (
            RenderRemedialSheetDocumentUseCase | None
        ) = None,
    ):
        self.work_repo = work_repo
        self.render_remedial_sheet_document_use_case = (
            render_remedial_sheet_document_use_case
            or RenderRemedialSheetDocumentUseCase(
                work_repo=work_repo,
                document_template_repo=document_template_repo,
                document_engine=document_engine,
            )
        )

    def execute(
        self,
        request: RenderRemedialSheetBatchDocumentRequest,
    ) -> DocumentRenderResult:
        work_name = self.work_repo.get_work_name(request.work_id)
        if work_name is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=request.options.renderer_type,
            )

        variant_ids = self.work_repo.get_work_remedial_variant_ids(
            request.work_id,
        )
        if not variant_ids:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_EMPTY,
                renderer_type=request.options.renderer_type,
                source_name=work_name,
            )

        files: List[GeneratedDocumentFile] = []
        file_type = ''
        for variant_id in variant_ids:
            result = self.render_remedial_sheet_document_use_case.execute(
                RenderRemedialSheetDocumentRequest(
                    variant_id=variant_id,
                    options=request.options,
                    template_spec=request.template_spec,
                )
            )
            if not result.success:
                return DocumentRenderResult(
                    status=result.status,
                    renderer_type=result.renderer_type,
                    file_type=result.file_type,
                    files=files,
                    source_name=work_name,
                )

            file_type = result.file_type
            files.extend(result.files)

        status = (
            DOCUMENT_RENDER_STATUS_GENERATED
            if files
            else DOCUMENT_RENDER_STATUS_EMPTY
        )
        return DocumentRenderResult(
            status=status,
            renderer_type=request.options.renderer_type,
            file_type=file_type,
            files=files,
            source_name=work_name,
        )
