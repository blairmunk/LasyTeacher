"""Legacy adapter for document print profile list data."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.use_cases.get_print_settings_list import (
    GetPrintSettingsListRequest,
    GetPrintSettingsListUseCase,
    PrintSettingsListData,
)


@dataclass(frozen=True)
class GetDocumentTemplateListRequest:
    template_type: str = ''
    document_type: str = ''

    @property
    def selected_document_type(self) -> str:
        return self.document_type or self.template_type


@dataclass(frozen=True)
class DocumentTemplateListData:
    print_profiles: List[PrintSettingsSpec]

    @property
    def templates(self) -> List[PrintSettingsSpec]:
        return self.print_profiles


class GetDocumentTemplateListUseCase(GetPrintSettingsListUseCase):
    """Adapt the former template-oriented list contract."""

    def __init__(
        self,
        document_template_repo: IPrintSettingsRepository | None = None,
        print_settings_repo: IPrintSettingsRepository | None = None,
    ):
        repository = print_settings_repo or document_template_repo
        super().__init__(print_settings_repo=repository)
        self.document_template_repo = repository

    def execute(
        self,
        request: GetDocumentTemplateListRequest | None = None,
    ) -> DocumentTemplateListData:
        request = request or GetDocumentTemplateListRequest()
        data = super().execute(
            GetPrintSettingsListRequest(
                document_type=request.selected_document_type,
            ),
        )
        return DocumentTemplateListData(print_profiles=data.print_profiles)
