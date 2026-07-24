"""Prepare data for the sectioned document print settings form."""

from core_logic.use_cases.get_document_template_form_data import (
    GetDocumentTemplateFormDataUseCase,
    GetPrintSettingsFormDataRequest,
    PrintSettingsFormData,
)


class GetPrintSettingsFormDataUseCase(GetDocumentTemplateFormDataUseCase):
    """Prepare data for the sectioned document print settings form."""
