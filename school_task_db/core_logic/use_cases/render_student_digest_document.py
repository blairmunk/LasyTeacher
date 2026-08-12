"""Render one batch document containing individual student digests."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
)
from core_logic.entities.student_digest import StudentDigestRequest
from core_logic.interfaces.presentation_profile_catalog_repo import (
    IPresentationProfileCatalogRepository,
)
from core_logic.use_cases.presentation_profile_selection import (
    resolve_document_presentation_profile,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeRequest,
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_recipe_factories import (
    build_student_digest_document_recipe_for_render,
)
from core_logic.value_objects.document_source_factories import (
    build_student_digest_document_source,
)
from core_logic.value_objects.document_recipes import (
    STUDENT_DIGEST_DOCUMENT_TYPE,
)


@dataclass(frozen=True)
class RenderStudentDigestDocumentRequest:
    digest_request: StudentDigestRequest
    render_target: RenderTarget
    presentation_profile: DocumentPresentationProfile | None = None
    presentation_profile_id: str = ''


class RenderStudentDigestDocumentUseCase:
    def __init__(
        self,
        get_student_digests_use_case,
        render_document_from_recipe_use_case: RenderDocumentFromRecipeUseCase,
        presentation_profile_repo: (
            IPresentationProfileCatalogRepository | None
        ) = None,
    ):
        self.get_student_digests_use_case = get_student_digests_use_case
        self.render_document_from_recipe_use_case = (
            render_document_from_recipe_use_case
        )
        self.presentation_profile_repo = presentation_profile_repo

    def execute(self, request):
        page = self.get_student_digests_use_case.execute(
            request.digest_request,
        )
        if page.selected_group is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=request.render_target.renderer_type,
            )
        if not page.digests:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_EMPTY,
                renderer_type=request.render_target.renderer_type,
                source_name=page.selected_group.name,
            )

        return self.render_document_from_recipe_use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=build_student_digest_document_source(
                    group_id=page.selected_group.pk,
                    group_name=page.selected_group.name,
                ),
                recipe=build_student_digest_document_recipe_for_render(
                    digest_request=request.digest_request,
                    student_ids=[
                        digest.student.pk for digest in page.digests
                    ],
                    presentation_profile=resolve_document_presentation_profile(
                        document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
                        request_presentation_profile=(
                            request.presentation_profile
                        ),
                        request_presentation_profile_id=(
                            request.presentation_profile_id
                        ),
                        presentation_profile_repo=(
                            self.presentation_profile_repo
                        ),
                    ),
                ),
                render_target=request.render_target,
                source_name=page.selected_group.name,
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
