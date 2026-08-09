"""Render document files for a remedial sheet."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DocumentRenderResult,
)
from core_logic.interfaces.presentation_profile_repo import (
    IPresentationProfileRepository,
)
from core_logic.interfaces.work_document_repo import IWorkDocumentRepository
from core_logic.use_cases.presentation_profile_selection import (
    resolve_document_presentation_profile,
)
from core_logic.use_cases.get_remedial_sheet_data import (
    GetRemedialSheetDataUseCase,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeRequest,
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
)
from core_logic.value_objects.document_render_recipe_factories import (
    build_remedial_sheet_document_recipe_for_render,
)
from core_logic.value_objects.document_source_factories import (
    build_remedial_sheet_document_source,
)
from core_logic.value_objects.document_recipes import REMEDIAL_SHEET_DOCUMENT_TYPE


@dataclass(frozen=True)
class RenderRemedialSheetDocumentRequest:
    variant_id: str
    options: RemedialSheetDocumentRenderOptions
    presentation_profile: DocumentPresentationProfile | None = None
    presentation_profile_id: str = ''


class RenderRemedialSheetDocumentUseCase:
    def __init__(
        self,
        work_repo: IWorkDocumentRepository,
        render_document_from_recipe_use_case: RenderDocumentFromRecipeUseCase,
        presentation_profile_repo: IPresentationProfileRepository | None = None,
    ):
        self.work_repo = work_repo
        self.render_document_from_recipe_use_case = (
            render_document_from_recipe_use_case
        )
        self.presentation_profile_repo = presentation_profile_repo
        self.get_sheet_data = GetRemedialSheetDataUseCase(work_repo)

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
        sheet_data = self.get_sheet_data.execute(request.variant_id)
        if sheet_data.status == 'not_found':
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=request.options.renderer_type,
            )
        if sheet_data.student is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
                renderer_type=request.options.renderer_type,
            )
        return self.render_document_from_recipe_use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=build_remedial_sheet_document_source(
                    request.variant_id,
                ),
                recipe=build_remedial_sheet_document_recipe_for_render(
                    options=request.options,
                    presentation_profile=resolve_document_presentation_profile(
                        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        request_presentation_profile=request.presentation_profile,
                        request_presentation_profile_id=request.presentation_profile_id,
                        presentation_profile_repo=self.presentation_profile_repo,
                    ),
                ),
                render_target=request.options.render_target,
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
