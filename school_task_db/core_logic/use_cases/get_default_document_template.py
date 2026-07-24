"""Legacy adapter for default document print settings."""

from dataclasses import dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.use_cases.get_default_print_settings import (
    DefaultPrintSettingsData,
    GetDefaultPrintSettingsRequest,
    GetDefaultPrintSettingsUseCase,
)


@dataclass(frozen=True)
class GetDefaultDocumentTemplateRequest:
    template_type: str
    document_type: str = ''

    @property
    def selected_document_type(self) -> str:
        return self.document_type or self.template_type


@dataclass(frozen=True)
class DefaultDocumentTemplateData:
    print_profile: PrintSettingsSpec | None = None

    @property
    def template(self) -> PrintSettingsSpec | None:
        return self.print_profile


class GetDefaultDocumentTemplateUseCase(GetDefaultPrintSettingsUseCase):
    """Adapt the former template-oriented default lookup contract."""

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
        request: GetDefaultDocumentTemplateRequest,
    ) -> DefaultDocumentTemplateData:
        data = super().execute(
            GetDefaultPrintSettingsRequest(
                document_type=request.selected_document_type,
            ),
        )
        return DefaultDocumentTemplateData(print_profile=data.print_profile)
