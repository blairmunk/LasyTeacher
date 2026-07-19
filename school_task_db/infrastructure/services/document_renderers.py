"""Legacy renderer adapters for section-based document requests."""

from core_logic.entities.document_generation import GeneratedDocument
from core_logic.interfaces.document_rendering import IDocumentRenderer
from core_logic.value_objects.document_render_plan import DocumentRenderRequest
from infrastructure.services.document_content_config import (
    content_config_from_document,
)


class LegacyDocumentRenderer(IDocumentRenderer):
    def __init__(
        self,
        file_type,
        source_getter,
        render_files,
        document_from_paths,
    ):
        self.file_type = file_type
        self.source_getter = source_getter
        self.render_files = render_files
        self.document_from_paths = document_from_paths

    def render(self, request: DocumentRenderRequest) -> GeneratedDocument:
        if request.document.source is None:
            raise ValueError('document source is required')

        source = self.source_getter(request.document.source.source_id)
        content_config = {
            **content_config_from_document(request.document),
            'page_format': request.render_target.page_format,
        }
        file_paths = self.render_files(
            source,
            content_config,
            request.render_target,
        )
        return self.document_from_paths(
            file_type=self.file_type,
            file_paths=file_paths,
        )
