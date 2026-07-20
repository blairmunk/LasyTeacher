"""Django document engine."""

from core_logic.entities.document_rendering import (
    GeneratedDocument,
    GeneratedFileResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.services.document_renderer_registry import (
    DocumentRendererRegistry,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderPlan,
    DocumentRenderRequest,
)
from infrastructure.services.django_document_source_provider import (
    DjangoDocumentSourceProvider,
)
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_defaults import (
    build_sectioned_document_components,
)


class DjangoDocumentEngine(IDocumentEngine):
    @classmethod
    def with_sectioned_renderers(
        cls,
        get_remedial_sheet_data_use_case=None,
        source_provider=None,
        file_store=None,
        template_renderer=None,
        html_to_pdf_renderer_factory=None,
    ):
        source_provider = source_provider or DjangoDocumentSourceProvider()
        file_store = file_store or RenderedDocumentFileStore()
        get_remedial_sheet_data = (
            get_remedial_sheet_data_use_case.execute
            if get_remedial_sheet_data_use_case
            else None
        )
        components = build_sectioned_document_components(
            file_store=file_store,
            get_work_source=source_provider.get_work_source,
            get_remedial_sheet_data=get_remedial_sheet_data,
            template_renderer=template_renderer,
            html_to_pdf_renderer_factory=html_to_pdf_renderer_factory,
        )
        return cls(
            document_builder=components.document_builder,
            document_renderer_registry=components.document_renderer_registry,
            file_store=file_store,
        )

    def __init__(
        self,
        document_builder=None,
        document_renderer_registry=None,
        file_store=None,
        section_payload_builder_registry=None,
    ):
        self.file_store = file_store or RenderedDocumentFileStore()
        self.document_builder = document_builder or RecipeDocumentBuilder(
            section_payload_builder_registry=section_payload_builder_registry,
        )
        self.document_renderer_registry = (
            document_renderer_registry
            or DocumentRendererRegistry()
        )

    def render_document(
        self,
        render_plan: DocumentRenderPlan,
    ) -> GeneratedDocument:
        if render_plan is None:
            raise ValueError('Document render plan is required.')
        render_target = render_plan.render_target
        document = self._build_document(render_plan)
        return self.document_renderer_registry.render(
            DocumentRenderRequest(
                document=document,
                render_target=render_target,
            )
        )

    def get_rendered_file(
        self,
        file_type: str,
        filename: str,
    ) -> GeneratedFileResult:
        return self.file_store.get_file(file_type, filename)

    def _build_document(self, render_plan=None):
        if render_plan is None:
            return None
        return self.document_builder.build(
            render_plan.source,
            render_plan.recipe,
            render_plan.render_target,
        )
