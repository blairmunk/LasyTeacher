"""Update document print settings."""

from core_logic.entities.document import (
    UpdatePrintSettingsParams,
    UpdatePrintSettingsResult,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.value_objects.document_section_catalog import (
    validate_document_section_specs,
)
from core_logic.value_objects.document_type_catalog import validate_document_type


PRINT_SETTINGS_UPDATE_STATUS_UPDATED = 'updated'
PRINT_SETTINGS_UPDATE_STATUS_INVALID = 'invalid'
PRINT_SETTINGS_UPDATE_STATUS_NOT_FOUND = 'not_found'


class UpdatePrintSettingsUseCase:
    """Validate and persist changes to document print settings."""

    def __init__(self, print_settings_repo: IPrintSettingsRepository):
        self.print_settings_repo = print_settings_repo

    def execute(
        self,
        params: UpdatePrintSettingsParams,
    ) -> UpdatePrintSettingsResult:
        errors = self._validate(params)
        if errors:
            return UpdatePrintSettingsResult(
                status=PRINT_SETTINGS_UPDATE_STATUS_INVALID,
                print_settings_id=params.print_settings_id,
                errors=tuple(errors),
            )

        updated = self.print_settings_repo.update_print_settings(params)
        if not updated:
            return UpdatePrintSettingsResult(
                status=PRINT_SETTINGS_UPDATE_STATUS_NOT_FOUND,
                print_settings_id=params.print_settings_id,
            )
        return UpdatePrintSettingsResult(
            status=PRINT_SETTINGS_UPDATE_STATUS_UPDATED,
            print_settings_id=params.print_settings_id,
        )

    def _validate(self, params: UpdatePrintSettingsParams) -> list[str]:
        errors = []
        if not params.print_settings_id:
            errors.append('ID профиля печати обязателен.')
        if not params.name:
            errors.append('Название профиля печати обязательно.')
        if not params.document_type:
            errors.append('Тип документа обязателен.')
        if not params.sections:
            errors.append('Выберите хотя бы одну секцию.')

        try:
            validate_document_type(params.document_type)
        except ValueError as error:
            errors.append(str(error))

        try:
            validate_document_section_specs(
                params.document_type,
                params.sections,
            )
        except ValueError as error:
            errors.append(str(error))

        return errors
