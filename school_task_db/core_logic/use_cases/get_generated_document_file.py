"""Return generated document file contents for download."""

from dataclasses import dataclass

from core_logic.entities.document_rendering import GeneratedFileResult
from core_logic.interfaces.document_engine import IDocumentEngine


@dataclass(frozen=True)
class GetGeneratedDocumentFileRequest:
    file_type: str
    filename: str


class GetGeneratedDocumentFileUseCase:
    def __init__(
        self,
        document_rendering_service: IDocumentEngine | None = None,
        document_generation_service: IDocumentEngine | None = None,
        document_engine: IDocumentEngine | None = None,
    ):
        self.document_engine = (
            document_engine
            or document_rendering_service
            or document_generation_service
        )
        self.document_rendering_service = self.document_engine

    def execute(
        self,
        request: GetGeneratedDocumentFileRequest,
    ) -> GeneratedFileResult:
        return self.document_engine.get_generated_file(
            file_type=request.file_type,
            filename=request.filename,
        )
