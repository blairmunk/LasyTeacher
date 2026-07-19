"""Return rendered document file contents for download."""

from dataclasses import dataclass

from core_logic.entities.document_rendering import GeneratedFileResult
from core_logic.interfaces.document_engine import IDocumentEngine


def resolve_document_engine(
    document_engine: IDocumentEngine | None = None,
    document_rendering_service: IDocumentEngine | None = None,
    document_generation_service: IDocumentEngine | None = None,
) -> IDocumentEngine:
    return (
        document_engine
        or document_rendering_service
        or document_generation_service
    )


@dataclass(frozen=True)
class GetRenderedDocumentFileRequest:
    file_type: str
    filename: str


class GetRenderedDocumentFileUseCase:
    def __init__(
        self,
        document_rendering_service: IDocumentEngine | None = None,
        document_generation_service: IDocumentEngine | None = None,
        document_engine: IDocumentEngine | None = None,
    ):
        self.document_engine = resolve_document_engine(
            document_engine=document_engine,
            document_rendering_service=document_rendering_service,
            document_generation_service=document_generation_service,
        )

    def execute(
        self,
        request: GetRenderedDocumentFileRequest,
    ) -> GeneratedFileResult:
        return self.document_engine.get_rendered_file(
            file_type=request.file_type,
            filename=request.filename,
        )
