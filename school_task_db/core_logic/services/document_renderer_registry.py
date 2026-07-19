"""Renderer registry for section-based documents."""

from core_logic.entities.document_generation import GeneratedDocument
from core_logic.interfaces.document_rendering import IDocumentRenderer
from core_logic.value_objects.document_render_plan import DocumentRenderRequest


class UnsupportedDocumentRenderer(ValueError):
    pass


class DocumentRendererRegistry(IDocumentRenderer):
    def __init__(self):
        self._renderers = {}

    def register(
        self,
        renderer_type: str,
        renderer: IDocumentRenderer,
    ) -> None:
        if not renderer_type:
            raise ValueError('renderer_type is required')
        self._renderers[renderer_type] = renderer

    def get(self, renderer_type: str) -> IDocumentRenderer:
        try:
            return self._renderers[renderer_type]
        except KeyError:
            raise UnsupportedDocumentRenderer(renderer_type)

    def render(self, request: DocumentRenderRequest) -> GeneratedDocument:
        renderer = self.get(request.render_target.renderer_type)
        return renderer.render(request)
