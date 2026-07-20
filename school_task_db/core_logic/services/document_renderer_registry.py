"""Renderer registry for section-based documents."""

from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.interfaces.document_rendering import (
    IDocumentRenderer,
    IDocumentSectionRenderer,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderRequest,
    DocumentSectionRenderRequest,
)


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

    def extend(self, registry: "DocumentRendererRegistry") -> None:
        self._renderers.update(registry._renderers)

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


class DocumentSectionRendererRegistry(IDocumentSectionRenderer):
    def __init__(self):
        self._renderers = {}

    def register(
        self,
        renderer_type: str,
        section_type: str,
        renderer: IDocumentSectionRenderer,
    ) -> None:
        if not renderer_type:
            raise ValueError('renderer_type is required')
        if not section_type:
            raise ValueError('section_type is required')
        self._renderers[(renderer_type, section_type)] = renderer

    def extend(self, registry: "DocumentSectionRendererRegistry") -> None:
        self._renderers.update(registry._renderers)

    def get(
        self,
        renderer_type: str,
        section_type: str,
    ) -> IDocumentSectionRenderer:
        try:
            return self._renderers[(renderer_type, section_type)]
        except KeyError:
            raise UnsupportedDocumentRenderer(
                f'{renderer_type}:{section_type}',
            )

    def render_section(self, request: DocumentSectionRenderRequest) -> str:
        renderer = self.get(
            renderer_type=request.render_target.renderer_type,
            section_type=request.section.section_type,
        )
        return renderer.render_section(request)
