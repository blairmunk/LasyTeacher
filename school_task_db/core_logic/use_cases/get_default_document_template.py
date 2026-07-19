"""Find the default document template for a document type."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)


@dataclass(frozen=True)
class GetDefaultDocumentTemplateRequest:
    template_type: str


@dataclass(frozen=True)
class DefaultDocumentTemplateData:
    template: DocumentTemplateSpec | None = None


class GetDefaultDocumentTemplateUseCase:
    def __init__(self, document_template_repo: IDocumentTemplateRepository):
        self.document_template_repo = document_template_repo

    def execute(
        self,
        request: GetDefaultDocumentTemplateRequest,
    ) -> DefaultDocumentTemplateData:
        return DefaultDocumentTemplateData(
            template=self.document_template_repo.get_default_template_spec(
                request.template_type,
            ),
        )
