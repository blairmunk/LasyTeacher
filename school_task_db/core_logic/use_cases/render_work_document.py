"""Render document files for a work."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED,
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
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan_factories import (
    build_work_document_recipe_for_render,
    build_work_document_source,
)
from core_logic.value_objects.document_recipes import WORK_DOCUMENT_TYPE


@dataclass(frozen=True)
class RenderWorkDocumentRequest:
    work_id: str
    options: WorkDocumentRenderOptions
    presentation_profile: DocumentPresentationProfile | None = None
    presentation_profile_id: str = ''
    variant_id: str = ''


class RenderWorkDocumentUseCase:
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
        request: RenderWorkDocumentRequest,
    ) -> DocumentRenderResult:
        renderer_type = request.options.renderer_type
        work = self.work_repo.get_work_document_ref(request.work_id)
        if work is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=renderer_type,
            )
        if work.work_type == 'remedial':
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED,
                renderer_type=renderer_type,
                source_name=work.name,
            )
        variant_ids = self.work_repo.get_work_variant_ids(request.work_id)
        if request.variant_id:
            if request.variant_id not in variant_ids:
                return DocumentRenderResult(
                    status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                    renderer_type=renderer_type,
                )
            variant_ids = [request.variant_id]

        return self.render_document_from_recipe_use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=build_work_document_source(
                    work_id=request.work_id,
                    work_name=work.name,
                ),
                recipe=build_work_document_recipe_for_render(
                    options=request.options,
                    presentation_profile=resolve_document_presentation_profile(
                        document_type=WORK_DOCUMENT_TYPE,
                        request_presentation_profile=request.presentation_profile,
                        request_presentation_profile_id=request.presentation_profile_id,
                        presentation_profile_repo=self.presentation_profile_repo,
                    ),
                    variant_ids=variant_ids,
                ),
                render_target=request.options.render_target,
                source_name=work.name,
                empty_status=DOCUMENT_RENDER_STATUS_GENERATED,
            )
        )
