"""Render one batch remedial sheet document for all remedial variants in a work."""

from dataclasses import InitVar, dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.use_cases.print_settings_selection import (
    resolve_document_print_settings_spec,
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
    print_settings_spec: PrintSettingsSpec | None = None
    print_settings_id: str = ''
    template_spec: InitVar[PrintSettingsSpec | None] = None
    template_id: InitVar[str] = ''

    def __post_init__(self, template_spec, template_id):
        if self.print_settings_spec is None and template_spec is not None:
            object.__setattr__(self, 'print_settings_spec', template_spec)
        if not self.print_settings_id and template_id:
            object.__setattr__(self, 'print_settings_id', template_id)


class RenderRemedialSheetBatchDocumentUseCase:
    def __init__(
        self,
        work_repo: IWorkRepository,
        print_settings_repo: IPrintSettingsRepository | None = None,
        document_template_repo: IPrintSettingsRepository | None = None,
        document_engine: IDocumentEngine | None = None,
        render_document_use_case: RenderDocumentUseCase | None = None,
    ):
        self.work_repo = work_repo
        self.print_settings_repo = print_settings_repo or document_template_repo
        self.document_template_repo = self.print_settings_repo
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
                    print_settings_spec=resolve_document_print_settings_spec(
                        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                        request_print_settings_spec=(
                            request.print_settings_spec
                        ),
                        request_print_settings_id=(
                            request.print_settings_id
                        ),
                        print_settings_repo=self.print_settings_repo,
                    ),
                ),
                source_name=work_name,
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
