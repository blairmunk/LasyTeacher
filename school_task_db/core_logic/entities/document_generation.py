"""Backward-compatible imports for document rendering DTOs."""

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_GENERATOR,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    DocumentGenerationResult,
    DocumentRenderResult,
    GENERATED_FILE_STATUS_NOT_FOUND,
    GENERATED_FILE_STATUS_READ_ERROR,
    GENERATED_FILE_STATUS_READY,
    GENERATED_FILE_STATUS_UNSUPPORTED_TYPE,
    GeneratedDocument,
    GeneratedDocumentFile,
    GeneratedFile,
    GeneratedFileResult,
)
