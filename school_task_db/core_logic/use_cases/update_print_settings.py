"""Update document print settings."""

from core_logic.use_cases.update_document_template import (
    DOCUMENT_TEMPLATE_UPDATE_STATUS_INVALID,
    DOCUMENT_TEMPLATE_UPDATE_STATUS_NOT_FOUND,
    DOCUMENT_TEMPLATE_UPDATE_STATUS_UPDATED,
    UpdateDocumentTemplateUseCase,
)


class UpdatePrintSettingsUseCase(UpdateDocumentTemplateUseCase):
    """Update document print settings."""
