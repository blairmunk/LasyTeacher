"""Legacy adapter for updating document print settings."""

from core_logic.entities.document import (
    UpdateDocumentTemplateParams,
    UpdateDocumentTemplateResult,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.use_cases.update_print_settings import (
    PRINT_SETTINGS_UPDATE_STATUS_INVALID,
    PRINT_SETTINGS_UPDATE_STATUS_NOT_FOUND,
    PRINT_SETTINGS_UPDATE_STATUS_UPDATED,
    UpdatePrintSettingsUseCase,
)


DOCUMENT_TEMPLATE_UPDATE_STATUS_UPDATED = PRINT_SETTINGS_UPDATE_STATUS_UPDATED
DOCUMENT_TEMPLATE_UPDATE_STATUS_INVALID = PRINT_SETTINGS_UPDATE_STATUS_INVALID
DOCUMENT_TEMPLATE_UPDATE_STATUS_NOT_FOUND = (
    PRINT_SETTINGS_UPDATE_STATUS_NOT_FOUND
)


class UpdateDocumentTemplateUseCase(UpdatePrintSettingsUseCase):
    """Adapt the former template-oriented update contract."""

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
        params: UpdateDocumentTemplateParams,
    ) -> UpdateDocumentTemplateResult:
        result = super().execute(params)
        return UpdateDocumentTemplateResult(
            status=result.status,
            template_id=result.print_settings_id,
            errors=result.errors,
        )
