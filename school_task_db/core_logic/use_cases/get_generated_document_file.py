"""Return generated document file contents for download."""

from dataclasses import dataclass

from core_logic.entities.document_rendering import GeneratedFileResult
from core_logic.interfaces.document_rendering_service import (
    IDocumentRenderingService,
)


@dataclass(frozen=True)
class GetGeneratedDocumentFileRequest:
    file_type: str
    filename: str


class GetGeneratedDocumentFileUseCase:
    def __init__(
        self,
        document_rendering_service: IDocumentRenderingService | None = None,
        document_generation_service: IDocumentRenderingService | None = None,
    ):
        self.document_rendering_service = (
            document_rendering_service or document_generation_service
        )

    def execute(
        self,
        request: GetGeneratedDocumentFileRequest,
    ) -> GeneratedFileResult:
        return self.document_rendering_service.get_generated_file(
            file_type=request.file_type,
            filename=request.filename,
        )
