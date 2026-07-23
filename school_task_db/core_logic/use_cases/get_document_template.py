"""Get one document print profile for editing."""

from dataclasses import dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)


@dataclass(frozen=True)
class GetDocumentTemplateRequest:
    template_id: str
    template_type: str = ''


@dataclass(frozen=True)
class GetDocumentTemplateData:
    print_profile: PrintSettingsSpec | None = None

    @property
    def template(self) -> PrintSettingsSpec | None:
        return self.print_profile


class GetDocumentTemplateUseCase:
    def __init__(
        self,
        document_template_repo: IDocumentTemplateRepository,
    ):
        self.document_template_repo = document_template_repo

    def execute(
        self,
        request: GetDocumentTemplateRequest,
    ) -> GetDocumentTemplateData:
        return GetDocumentTemplateData(
            print_profile=self.document_template_repo.get_template_spec(
                template_id=request.template_id,
                template_type=request.template_type,
            )
        )
