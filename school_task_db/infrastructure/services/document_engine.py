"""Infrastructure orchestration for section-based document rendering."""

from core_logic.entities.document_rendering import (
    GeneratedDocument,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.services.document_renderer_registry import (
    DocumentRendererRegistry,
)
from core_logic.value_objects.document_render_plan import DocumentRenderPlan
from core_logic.value_objects.document_render_requests import DocumentRenderRequest


class SectionedDocumentEngine(IDocumentEngine):
    """Build a document from its recipe and dispatch it to a renderer."""

    def __init__(
        self,
        document_builder=None,
        document_renderer_registry=None,
        section_payload_builder_registry=None,
    ):
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

    def _build_document(self, render_plan: DocumentRenderPlan):
        return self.document_builder.build(
            render_plan.source,
            render_plan.recipe,
            render_plan.render_target,
        )
