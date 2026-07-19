"""Backward-compatible imports for document rendering service."""

from core_logic.interfaces.document_rendering_service import (
    IDocumentRenderingService,
)


IDocumentGenerationService = IDocumentRenderingService
