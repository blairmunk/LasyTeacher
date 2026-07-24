"""Render document files for a remedial sheet."""

from dataclasses import InitVar, dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
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
    build_remedial_sheet_document_render_plan,
)
from core_logic.value_objects.document_recipes import REMEDIAL_SHEET_DOCUMENT_TYPE


@dataclass(frozen=True)
class RenderRemedialSheetDocumentRequest:
    variant_id: str
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


class RenderRemedialSheetDocumentUseCase:
    def __init__(
        self,
        work_repo: IWorkRepository | None = None,
        print_settings_repo: IPrintSettingsRepository | None = None,
        document_template_repo: IPrintSettingsRepository | None = None,
        document_engine: IDocumentEngine | None = None,
        render_document_use_case: RenderDocumentUseCase | None = None,
    ):
        if render_document_use_case is not None:
            self.render_document_use_case = render_document_use_case
        else:
            self.render_document_use_case = RenderDocumentUseCase(
                document_engine=document_engine,
            )
        self.work_repo = work_repo
        self.print_settings_repo = print_settings_repo or document_template_repo
        self.document_template_repo = self.print_settings_repo

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
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )
