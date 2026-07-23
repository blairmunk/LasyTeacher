"""Build document print profile list data."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
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


class GetDocumentTemplateListUseCase:
    def __init__(
        self,
        print_settings_repo: IPrintSettingsRepository | None = None,
        document_template_repo: IPrintSettingsRepository | None = None,
    ):
        self.print_settings_repo = print_settings_repo or document_template_repo
        self.document_template_repo = self.print_settings_repo

    def execute(
        self,
        request: GetDocumentTemplateListRequest | None = None,
    ) -> DocumentTemplateListData:
        request = request or GetDocumentTemplateListRequest()
        return DocumentTemplateListData(
            print_profiles=self.print_settings_repo.list_print_settings_specs(
                document_type=request.selected_document_type,
            ),
        )


GetPrintSettingsListRequest = GetDocumentTemplateListRequest
PrintSettingsListData = DocumentTemplateListData
GetPrintSettingsListUseCase = GetDocumentTemplateListUseCase
