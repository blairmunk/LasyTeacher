"""Update a document print profile.

The module name is legacy; persistence is still backed by document templates.
"""

from core_logic.entities.document import (
    UpdatePrintSettingsParams,
    UpdatePrintSettingsResult,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.value_objects.document_section_catalog import (
    validate_document_section_types,
)
from core_logic.value_objects.document_type_catalog import validate_document_type


DOCUMENT_TEMPLATE_UPDATE_STATUS_UPDATED = 'updated'
DOCUMENT_TEMPLATE_UPDATE_STATUS_INVALID = 'invalid'
DOCUMENT_TEMPLATE_UPDATE_STATUS_NOT_FOUND = 'not_found'


class UpdateDocumentTemplateUseCase:
    def __init__(
        self,
        print_settings_repo: IPrintSettingsRepository | None = None,
        document_template_repo: IPrintSettingsRepository | None = None,
    ):
        self.print_settings_repo = print_settings_repo or document_template_repo
        self.document_template_repo = self.print_settings_repo

    def execute(
        self,
        params: UpdatePrintSettingsParams,
    ) -> UpdatePrintSettingsResult:
        errors = self._validate(params)
        if errors:
            return UpdatePrintSettingsResult(
                status=DOCUMENT_TEMPLATE_UPDATE_STATUS_INVALID,
                template_id=params.template_id,
                errors=tuple(errors),
            )

        updated = self.print_settings_repo.update_print_settings(params)
        if not updated:
            return UpdatePrintSettingsResult(
                status=DOCUMENT_TEMPLATE_UPDATE_STATUS_NOT_FOUND,
                template_id=params.template_id,
            )
        return UpdatePrintSettingsResult(
            status=DOCUMENT_TEMPLATE_UPDATE_STATUS_UPDATED,
            template_id=params.template_id,
        )

    def _validate(self, params: UpdatePrintSettingsParams) -> list[str]:
        errors = []
        if not params.template_id:
            errors.append('ID профиля печати обязателен.')
        if not params.name:
            errors.append('Название профиля печати обязательно.')
        if not params.template_type:
            errors.append('Тип документа обязателен.')
        if not params.section_types:
            errors.append('Выберите хотя бы одну секцию.')

        try:
            validate_document_type(params.template_type)
        except ValueError as error:
            errors.append(str(error))

        try:
            validate_document_section_types(
                params.template_type,
                params.section_types,
                include_legacy=False,
            )
        except ValueError as error:
            errors.append(str(error))

        return errors


UpdatePrintSettingsUseCase = UpdateDocumentTemplateUseCase
