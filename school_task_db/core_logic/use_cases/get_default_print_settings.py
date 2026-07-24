"""Find the default document print settings for a document type."""

from core_logic.use_cases.get_default_document_template import (
    DefaultPrintSettingsData,
    GetDefaultDocumentTemplateUseCase,
    GetDefaultPrintSettingsRequest,
)


class GetDefaultPrintSettingsUseCase(GetDefaultDocumentTemplateUseCase):
    """Find the default document print settings for a document type."""
