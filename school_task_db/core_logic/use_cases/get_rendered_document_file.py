"""Return rendered document file contents for download."""

from dataclasses import dataclass

from core_logic.entities.document_rendering import GeneratedFileResult
from core_logic.interfaces.rendered_document_file_store import (
    IRenderedDocumentFileStore,
)


@dataclass(frozen=True)
class GetRenderedDocumentFileRequest:
    file_type: str
    filename: str


class GetRenderedDocumentFileUseCase:
    def __init__(
        self,
        file_store: IRenderedDocumentFileStore | None = None,
    ):
        if file_store is None:
            raise ValueError('Rendered document file store is required.')
        self.file_store = file_store

    def execute(
        self,
        request: GetRenderedDocumentFileRequest,
    ) -> GeneratedFileResult:
        return self.file_store.get_file(
            file_type=request.file_type,
            filename=request.filename,
        )
