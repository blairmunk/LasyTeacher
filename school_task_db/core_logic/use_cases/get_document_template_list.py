"""Build document print profile list data."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)


@dataclass(frozen=True)
class GetDocumentTemplateListRequest:
    template_type: str = ''


@dataclass(frozen=True)
class DocumentTemplateListData:
    print_profiles: List[PrintSettingsSpec]

    @property
    def templates(self) -> List[PrintSettingsSpec]:
        return self.print_profiles


class GetDocumentTemplateListUseCase:
    def __init__(self, document_template_repo: IDocumentTemplateRepository):
        self.document_template_repo = document_template_repo

    def execute(
        self,
        request: GetDocumentTemplateListRequest | None = None,
    ) -> DocumentTemplateListData:
        request = request or GetDocumentTemplateListRequest()
        return DocumentTemplateListData(
            print_profiles=self.document_template_repo.list_print_settings_specs(
                document_type=request.template_type,
            ),
        )
