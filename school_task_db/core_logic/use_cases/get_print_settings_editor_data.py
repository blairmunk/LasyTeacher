"""Prepare data for the sectioned document print settings editor."""

from core_logic.use_cases.get_document_template_editor_data import (
    GetDocumentTemplateEditorDataUseCase,
    GetPrintSettingsEditorDataRequest,
    PrintSettingsEditorData,
)


class GetPrintSettingsEditorDataUseCase(GetDocumentTemplateEditorDataUseCase):
    """Prepare data for the sectioned document print settings editor."""
