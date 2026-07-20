"""Render document files for a remedial sheet."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
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
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan_factories import (
    build_remedial_sheet_document_render_plan,
)
from core_logic.value_objects.document_recipes import REMEDIAL_SHEET_DOCUMENT_TYPE


@dataclass(frozen=True)
class RenderRemedialSheetDocumentRequest:
    variant_id: str
    options: RemedialSheetDocumentRenderOptions
    template_spec: DocumentTemplateSpec | None = None


class RenderRemedialSheetDocumentUseCase:
    def __init__(
        self,
        work_repo: IWorkRepository | None = None,
        document_template_repo: IDocumentTemplateRepository | None = None,
        document_engine: IDocumentEngine | None = None,
        render_document_use_case: RenderDocumentUseCase | None = None,
        render_document_from_recipe_use_case: (
            RenderDocumentFromRecipeUseCase | None
        ) = None,
    ):
        if render_document_use_case is not None:
            self.render_document_use_case = render_document_use_case
        elif render_document_from_recipe_use_case is not None:
            self.render_document_use_case = (
                render_document_from_recipe_use_case.render_document_use_case
            )
        else:
            self.render_document_use_case = RenderDocumentUseCase(
                document_engine=document_engine,
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
        return self.render_document_use_case.execute(
            RenderDocumentRequest(
                render_plan=build_remedial_sheet_document_render_plan(
                    variant_id=request.variant_id,
                    options=request.options,
                    template_spec=resolve_document_template_spec(
                        template_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        request_template_spec=request.template_spec,
                        document_template_repo=self.document_template_repo,
                    ),
                ),
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
