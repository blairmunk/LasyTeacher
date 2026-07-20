"""Return rendered document file contents for download."""

from dataclasses import dataclass

from core_logic.entities.document_rendering import GeneratedFileResult
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.use_cases.document_engine_dependency import resolve_document_engine


@dataclass(frozen=True)
class GetRenderedDocumentFileRequest:
    file_type: str
    filename: str


class GetRenderedDocumentFileUseCase:
    def __init__(
        self,
        document_engine: IDocumentEngine | None = None,
    ):
        self.document_engine = resolve_document_engine(
            document_engine=document_engine,
        )

    def execute(
        self,
        request: GetRenderedDocumentFileRequest,
    ) -> GeneratedFileResult:
        return self.document_engine.get_rendered_file(
            file_type=request.file_type,
            filename=request.filename,
        )
