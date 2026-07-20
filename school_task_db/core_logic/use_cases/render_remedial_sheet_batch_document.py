"""Render one batch remedial sheet document for all remedial variants in a work."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.use_cases.document_template_selection import (
    resolve_document_template_spec,
)
from core_logic.use_cases.render_document import (
    RenderDocumentRequest,
    RenderDocumentUseCase,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan_factories import (
    build_remedial_sheet_batch_document_render_plan,
)
from core_logic.value_objects.document_recipes import REMEDIAL_SHEET_DOCUMENT_TYPE


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
        render_document_use_case: RenderDocumentUseCase | None = None,
    ):
        self.work_repo = work_repo
        self.document_template_repo = document_template_repo
        self.render_document_use_case = (
            render_document_use_case
            or RenderDocumentUseCase(
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

        return self.render_document_use_case.execute(
            RenderDocumentRequest(
                render_plan=build_remedial_sheet_batch_document_render_plan(
                    work_id=request.work_id,
                    work_name=work_name,
                    variant_ids=variant_ids,
                    options=request.options,
                    template_spec=resolve_document_template_spec(
                        template_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        request_template_spec=request.template_spec,
                        document_template_repo=self.document_template_repo,
                    ),
                ),
                source_name=work_name,
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
