"""Legacy adapter for reading one document print profile."""

from dataclasses import dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.use_cases.get_print_settings import (
    GetPrintSettingsData,
    GetPrintSettingsRequest,
    GetPrintSettingsUseCase,
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


class GetDocumentTemplateUseCase(GetPrintSettingsUseCase):
    """Adapt the former template-oriented request and response."""

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
        request: GetDocumentTemplateRequest,
    ) -> GetDocumentTemplateData:
        data = super().execute(
            GetPrintSettingsRequest(
                print_settings_id=request.selected_print_settings_id,
                document_type=request.selected_document_type,
            ),
        )
        return GetDocumentTemplateData(print_profile=data.print_profile)
