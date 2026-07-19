"""Backward-compatible imports for rendered document file download use case."""

from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileRequest,
    GetRenderedDocumentFileUseCase,
)


GetGeneratedDocumentFileRequest = GetRenderedDocumentFileRequest
GetGeneratedDocumentFileUseCase = GetRenderedDocumentFileUseCase
