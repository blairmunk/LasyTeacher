"""Render document files for a remedial sheet."""

from dataclasses import dataclass, field

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DocumentRenderResult,
)
from core_logic.interfaces.presentation_profile_catalog_repo import (
    IPresentationProfileCatalogRepository,
)
from core_logic.interfaces.remedial_sheet_repo import IRemedialSheetRepository
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
    RemedialSheetPrintOptions,
    RenderTarget,
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
    render_target: RenderTarget = field(default_factory=RenderTarget)
    print_options: RemedialSheetPrintOptions = field(
        default_factory=RemedialSheetPrintOptions,
    )
    presentation_profile: DocumentPresentationProfile | None = None
    presentation_profile_id: str = ''


class RenderRemedialSheetDocumentUseCase:
    def __init__(
        self,
        remedial_repo: IRemedialSheetRepository,
        render_document_from_recipe_use_case: RenderDocumentFromRecipeUseCase,
        presentation_profile_repo: (
            IPresentationProfileCatalogRepository | None
        ) = None,
    ):
        self.remedial_repo = remedial_repo
        self.render_document_from_recipe_use_case = (
            render_document_from_recipe_use_case
        )
        self.presentation_profile_repo = presentation_profile_repo
        self.get_sheet_data = GetRemedialSheetDataUseCase(remedial_repo)

    def execute(
        self,
        request: RenderRemedialSheetDocumentRequest,
    ) -> DocumentRenderResult:
        variant_type = self.remedial_repo.get_variant_type(request.variant_id)
        if variant_type is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=request.render_target.renderer_type,
            )
        if variant_type != 'remedial':
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
                renderer_type=request.render_target.renderer_type,
            )
        sheet_data = self.get_sheet_data.execute(request.variant_id)
        if sheet_data.status == 'not_found':
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=request.render_target.renderer_type,
            )
        if sheet_data.student is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
                renderer_type=request.render_target.renderer_type,
            )
        return self.render_document_from_recipe_use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=build_remedial_sheet_document_source(
                    request.variant_id,
                ),
                recipe=build_remedial_sheet_document_recipe_for_render(
                    print_options=request.print_options,
                    presentation_profile=resolve_document_presentation_profile(
                        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        request_presentation_profile=request.presentation_profile,
                        request_presentation_profile_id=request.presentation_profile_id,
                        presentation_profile_repo=self.presentation_profile_repo,
                    ),
                ),
                render_target=request.render_target,
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
