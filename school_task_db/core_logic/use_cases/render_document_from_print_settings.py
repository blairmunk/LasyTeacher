"""Render a sectioned document from explicit print settings."""

from core_logic.use_cases.render_document_from_template import (
    RenderDocumentFromTemplateRequest,
    RenderDocumentFromTemplateUseCase,
)


class RenderDocumentFromPrintSettingsRequest(RenderDocumentFromTemplateRequest):
    """Request to render a document from print settings."""


class RenderDocumentFromPrintSettingsUseCase(RenderDocumentFromTemplateUseCase):
    """Render a sectioned document from print settings."""
