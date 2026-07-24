"""Legacy adapter for creating document print settings."""

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    CreateDocumentTemplateResult,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.use_cases.create_print_settings import (
    PRINT_SETTINGS_CREATE_STATUS_CREATED,
    PRINT_SETTINGS_CREATE_STATUS_INVALID,
    CreatePrintSettingsUseCase,
)


DOCUMENT_TEMPLATE_CREATE_STATUS_CREATED = PRINT_SETTINGS_CREATE_STATUS_CREATED
DOCUMENT_TEMPLATE_CREATE_STATUS_INVALID = PRINT_SETTINGS_CREATE_STATUS_INVALID


class CreateDocumentTemplateUseCase(CreatePrintSettingsUseCase):
    """Adapt the former template-oriented create contract."""

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
        params: CreateDocumentTemplateParams,
    ) -> CreateDocumentTemplateResult:
        result = super().execute(params)
        return CreateDocumentTemplateResult(
            status=result.status,
            template_id=result.print_settings_id,
            errors=result.errors,
        )
