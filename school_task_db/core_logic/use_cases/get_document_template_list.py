"""Build document template list data."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)


@dataclass(frozen=True)
class GetDocumentTemplateListRequest:
    template_type: str = ''


@dataclass(frozen=True)
class DocumentTemplateListData:
    templates: List[DocumentTemplateSpec]


class GetDocumentTemplateListUseCase:
    def __init__(self, document_template_repo: IDocumentTemplateRepository):
        self.document_template_repo = document_template_repo

    def execute(
        self,
        request: GetDocumentTemplateListRequest | None = None,
    ) -> DocumentTemplateListData:
        request = request or GetDocumentTemplateListRequest()
        return DocumentTemplateListData(
            templates=self.document_template_repo.list_template_specs(
                template_type=request.template_type,
            ),
        )
