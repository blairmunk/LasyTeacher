"""Render section-based document content into a generated text file."""

from typing import Callable

from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.interfaces.document_rendering import IDocumentRenderer
from core_logic.value_objects.document_render_plan import DocumentRenderRequest


class SectionedDocumentFileRenderer(IDocumentRenderer):
    def __init__(
        self,
        file_type: str,
        filename_builder: Callable[[DocumentRenderRequest], str],
        content_renderer,
        file_store,
    ):
        if not file_type:
            raise ValueError('file_type is required')

        self.file_type = file_type
        self.filename_builder = filename_builder
        self.content_renderer = content_renderer
        self.file_store = file_store

    def render(self, request: DocumentRenderRequest) -> GeneratedDocument:
        filename = self.filename_builder(request)
        if not filename:
            raise ValueError('filename is required')

        content = self.content_renderer.render_content(request)
        return self.file_store.write_text_document(
            file_type=self.file_type,
            filename=filename,
            content=content,
        )
