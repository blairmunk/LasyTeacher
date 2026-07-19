"""Renderer registry for section-based documents."""

from core_logic.entities.document_rendering import GeneratedDocument
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
        document_type: str = '',
    ) -> None:
        if not renderer_type:
            raise ValueError('renderer_type is required')
        self._renderers[(document_type, renderer_type)] = renderer

    def get(
        self,
        renderer_type: str,
        document_type: str = '',
    ) -> IDocumentRenderer:
        try:
            return self._renderers[(document_type, renderer_type)]
        except KeyError:
            raise UnsupportedDocumentRenderer(renderer_type)

    def render(self, request: DocumentRenderRequest) -> GeneratedDocument:
        renderer = self.get(
            renderer_type=request.render_target.renderer_type,
            document_type=request.document.document_type,
        )
        return renderer.render(request)
