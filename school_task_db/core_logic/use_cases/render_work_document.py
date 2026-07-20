"""Render document files for a work."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.use_cases.document_engine_dependency import resolve_document_engine
from core_logic.use_cases.document_template_selection import (
    resolve_document_template_spec,
)
from core_logic.use_cases.render_document import (
    RenderDocumentRequest,
    RenderDocumentUseCase,
)
from core_logic.value_objects.document_render_options import (
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan_factories import (
    build_work_document_render_plan,
)
from core_logic.value_objects.document_recipes import WORK_DOCUMENT_TYPE


@dataclass(frozen=True)
class RenderWorkDocumentRequest:
    work_id: str
    options: WorkDocumentRenderOptions
    template_spec: DocumentTemplateSpec | None = None


class RenderWorkDocumentUseCase:
    def __init__(
        self,
        work_repo: IWorkRepository | None = None,
        document_template_repo: IDocumentTemplateRepository | None = None,
        document_engine: IDocumentEngine | None = None,
    ):
        self.document_engine = resolve_document_engine(
            document_engine=document_engine,
        )
        self.render_document_use_case = RenderDocumentUseCase(
            document_engine=self.document_engine,
        )
        self.work_repo = work_repo
        self.document_template_repo = document_template_repo

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

        render_plan = build_work_document_render_plan(
            work_id=request.work_id,
            work_name=work_name,
            options=request.options,
            template_spec=resolve_document_template_spec(
                template_type=WORK_DOCUMENT_TYPE,
                request_template_spec=request.template_spec,
                document_template_repo=self.document_template_repo,
            ),
        )
        return self.render_document_use_case.execute(
            RenderDocumentRequest(
                render_plan=render_plan,
                source_name=work_name,
                empty_status=DOCUMENT_RENDER_STATUS_GENERATED,
            )
        )
