"""Render one batch remedial sheet document for all remedial variants in a work."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
)
from core_logic.interfaces.presentation_profile_repo import (
    IPresentationProfileRepository,
)
from core_logic.interfaces.work_document_repo import IWorkDocumentRepository
from core_logic.use_cases.presentation_profile_selection import (
    resolve_document_presentation_profile,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeRequest,
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
)
from core_logic.value_objects.document_render_recipe_factories import (
    build_remedial_sheet_batch_document_recipe_for_render,
)
from core_logic.value_objects.document_source_factories import (
    build_remedial_sheet_batch_document_source,
)
from core_logic.value_objects.document_recipes import REMEDIAL_SHEET_DOCUMENT_TYPE


@dataclass(frozen=True)
class RenderRemedialSheetBatchDocumentRequest:
    work_id: str
    options: RemedialSheetDocumentRenderOptions
    presentation_profile: DocumentPresentationProfile | None = None
    presentation_profile_id: str = ''


class RenderRemedialSheetBatchDocumentUseCase:
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

    def execute(
        self,
        request: RenderRemedialSheetBatchDocumentRequest,
    ) -> DocumentRenderResult:
        work = self.work_repo.get_work_document_ref(request.work_id)
        if work is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=request.options.renderer_type,
            )

        variant_ids = self.work_repo.get_work_personal_remedial_variant_ids(
            request.work_id,
        )
        if not variant_ids:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_EMPTY,
                renderer_type=request.options.renderer_type,
                source_name=work.name,
            )

        return self.render_document_from_recipe_use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=build_remedial_sheet_batch_document_source(
                    work_id=request.work_id,
                    work_name=work.name,
                ),
                recipe=build_remedial_sheet_batch_document_recipe_for_render(
                    variant_ids=variant_ids,
                    build_options=request.options.build_options,
                    presentation_profile=resolve_document_presentation_profile(
                        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        request_presentation_profile=request.presentation_profile,
                        request_presentation_profile_id=request.presentation_profile_id,
                        presentation_profile_repo=self.presentation_profile_repo,
                    ),
                ),
                render_target=request.options.render_target,
                source_name=work.name,
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
