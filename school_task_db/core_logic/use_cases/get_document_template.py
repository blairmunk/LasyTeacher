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
    print_settings_id: str = ''
    document_type: str = ''

    @property
    def selected_print_settings_id(self) -> str:
        return self.print_settings_id or self.template_id

    @property
    def selected_document_type(self) -> str:
        return self.document_type or self.template_type


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
            print_profile=self.document_template_repo.get_print_settings_spec(
                print_settings_id=request.selected_print_settings_id,
                document_type=request.selected_document_type,
            )
        )


GetPrintSettingsRequest = GetDocumentTemplateRequest
GetPrintSettingsData = GetDocumentTemplateData
GetPrintSettingsUseCase = GetDocumentTemplateUseCase
