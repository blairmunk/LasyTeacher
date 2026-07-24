"""Get one document print settings profile for editing."""

from core_logic.use_cases.get_document_template import (
    GetDocumentTemplateUseCase,
    GetPrintSettingsData,
    GetPrintSettingsRequest,
)


class GetPrintSettingsUseCase(GetDocumentTemplateUseCase):
    """Get one document print settings profile for editing."""
