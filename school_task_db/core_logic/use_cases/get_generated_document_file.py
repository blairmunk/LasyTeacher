"""Return generated document file contents for download."""

from dataclasses import dataclass

from core_logic.entities.document_generation import GeneratedFileResult
from core_logic.interfaces.document_generation import IDocumentGenerationService


@dataclass(frozen=True)
class GetGeneratedDocumentFileRequest:
    file_type: str
    filename: str


class GetGeneratedDocumentFileUseCase:
    def __init__(self, document_generation_service: IDocumentGenerationService):
        self.document_generation_service = document_generation_service

    def execute(
        self,
        request: GetGeneratedDocumentFileRequest,
    ) -> GeneratedFileResult:
        return self.document_generation_service.get_generated_file(
            file_type=request.file_type,
            filename=request.filename,
        )
