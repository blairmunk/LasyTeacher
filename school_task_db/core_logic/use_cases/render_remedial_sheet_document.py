"""Render document files for a remedial sheet."""

from dataclasses import dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DocumentRenderResult,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.interfaces.work_document_repo import IWorkDocumentRepository
from core_logic.use_cases.print_settings_selection import (
    resolve_document_print_settings_spec,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeRequest,
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan_factories import (
    build_remedial_sheet_document_recipe_for_render,
    build_remedial_sheet_document_source,
)
from core_logic.value_objects.document_recipes import REMEDIAL_SHEET_DOCUMENT_TYPE


@dataclass(frozen=True)
class RenderRemedialSheetDocumentRequest:
    variant_id: str
    options: RemedialSheetDocumentRenderOptions
    print_settings_spec: PrintSettingsSpec | None = None
    print_settings_id: str = ''


class RenderRemedialSheetDocumentUseCase:
    def __init__(
        self,
        work_repo: IWorkDocumentRepository,
        render_document_from_recipe_use_case: RenderDocumentFromRecipeUseCase,
        print_settings_repo: IPrintSettingsRepository | None = None,
    ):
        self.work_repo = work_repo
        self.render_document_from_recipe_use_case = (
            render_document_from_recipe_use_case
        )
        self.print_settings_repo = print_settings_repo

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
        return self.render_document_from_recipe_use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=build_remedial_sheet_document_source(
                    request.variant_id,
                ),
                recipe=build_remedial_sheet_document_recipe_for_render(
                    options=request.options,
                    print_settings_spec=resolve_document_print_settings_spec(
                        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        request_print_settings_spec=request.print_settings_spec,
                        request_print_settings_id=request.print_settings_id,
                        print_settings_repo=self.print_settings_repo,
                    ),
                ),
                render_target=request.options.render_target,
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
