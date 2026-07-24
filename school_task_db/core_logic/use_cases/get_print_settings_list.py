"""Build document print settings list data."""

from core_logic.use_cases.get_document_template_list import (
    GetDocumentTemplateListUseCase,
    GetPrintSettingsListRequest,
    PrintSettingsListData,
)


class GetPrintSettingsListUseCase(GetDocumentTemplateListUseCase):
    """Build document print settings list data."""
