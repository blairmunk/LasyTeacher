"""Find the default document print profile for a document type."""

from dataclasses import dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)


@dataclass(frozen=True)
class GetDefaultDocumentTemplateRequest:
    template_type: str


@dataclass(frozen=True)
class DefaultDocumentTemplateData:
    print_profile: PrintSettingsSpec | None = None

    @property
    def template(self) -> PrintSettingsSpec | None:
        return self.print_profile


class GetDefaultDocumentTemplateUseCase:
    def __init__(self, document_template_repo: IDocumentTemplateRepository):
        self.document_template_repo = document_template_repo

    def execute(
        self,
        request: GetDefaultDocumentTemplateRequest,
    ) -> DefaultDocumentTemplateData:
        return DefaultDocumentTemplateData(
            print_profile=self.document_template_repo.get_default_template_spec(
                request.template_type,
            ),
        )
