"""Render document files for a work."""

from dataclasses import dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
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
    print_settings_spec: PrintSettingsSpec | None = None
    print_settings_id: str = ''
    variant_id: str = ''


class RenderWorkDocumentUseCase:
    def __init__(
        self,
        work_repo: IWorkDocumentRepository | None = None,
        print_settings_repo: IPrintSettingsRepository | None = None,
        document_engine: IDocumentEngine | None = None,
        render_document_from_recipe_use_case: (
            RenderDocumentFromRecipeUseCase | None
        ) = None,
    ):
        self.render_document_from_recipe_use_case = (
            render_document_from_recipe_use_case
            or RenderDocumentFromRecipeUseCase(
                document_engine=document_engine,
            )
        )
        self.work_repo = work_repo
        self.print_settings_repo = print_settings_repo

    def execute(
        self,
        request: RenderWorkDocumentRequest,
    ) -> DocumentRenderResult:
        renderer_type = request.options.renderer_type
        work_name = self.work_repo.get_work_name(request.work_id)
        if work_name is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=renderer_type,
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
                    work_name=work_name,
                ),
                recipe=build_work_document_recipe_for_render(
                    options=request.options,
                    print_settings_spec=resolve_document_print_settings_spec(
                        document_type=WORK_DOCUMENT_TYPE,
                        request_print_settings_spec=request.print_settings_spec,
                        request_print_settings_id=request.print_settings_id,
                        print_settings_repo=self.print_settings_repo,
                    ),
                    variant_ids=variant_ids,
                ),
                render_target=request.options.render_target,
                source_name=work_name,
                empty_status=DOCUMENT_RENDER_STATUS_GENERATED,
            )
        )
