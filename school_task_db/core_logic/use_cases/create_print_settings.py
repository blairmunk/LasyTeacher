"""Create document print settings."""

from core_logic.entities.document import (
    CreatePrintSettingsParams,
    CreatePrintSettingsResult,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.value_objects.document_section_catalog import (
    validate_document_section_types,
)
from core_logic.value_objects.document_type_catalog import validate_document_type


PRINT_SETTINGS_CREATE_STATUS_CREATED = 'created'
PRINT_SETTINGS_CREATE_STATUS_INVALID = 'invalid'


class CreatePrintSettingsUseCase:
    """Validate and persist a document print settings profile."""

    def __init__(self, print_settings_repo: IPrintSettingsRepository):
        self.print_settings_repo = print_settings_repo

    def execute(
        self,
        params: CreatePrintSettingsParams,
    ) -> CreatePrintSettingsResult:
        errors = self._validate(params)
        if errors:
            return CreatePrintSettingsResult(
                status=PRINT_SETTINGS_CREATE_STATUS_INVALID,
                errors=tuple(errors),
            )

        print_settings_id = self.print_settings_repo.create_print_settings(
            params,
        )
        return CreatePrintSettingsResult(
            status=PRINT_SETTINGS_CREATE_STATUS_CREATED,
            print_settings_id=print_settings_id,
        )

    def _validate(self, params: CreatePrintSettingsParams) -> list[str]:
        errors = []
        if not params.name:
            errors.append('Название профиля печати обязательно.')
        if not params.document_type:
            errors.append('Тип документа обязателен.')
        if not params.section_types:
            errors.append('Выберите хотя бы одну секцию.')

        try:
            validate_document_type(params.document_type)
        except ValueError as error:
            errors.append(str(error))

        try:
            validate_document_section_types(
                params.document_type,
                params.section_types,
            )
        except ValueError as error:
            errors.append(str(error))

        return errors
