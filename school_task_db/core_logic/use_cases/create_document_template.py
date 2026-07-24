"""Create a document print profile.

The module name is legacy; persistence is still backed by document templates.
"""

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


DOCUMENT_TEMPLATE_CREATE_STATUS_CREATED = 'created'
DOCUMENT_TEMPLATE_CREATE_STATUS_INVALID = 'invalid'


class CreateDocumentTemplateUseCase:
    def __init__(
        self,
        print_settings_repo: IPrintSettingsRepository | None = None,
        document_template_repo: IPrintSettingsRepository | None = None,
    ):
        self.print_settings_repo = print_settings_repo or document_template_repo
        self.document_template_repo = self.print_settings_repo

    def execute(
        self,
        params: CreatePrintSettingsParams,
    ) -> CreatePrintSettingsResult:
        errors = self._validate(params)
        if errors:
            return CreatePrintSettingsResult(
                status=DOCUMENT_TEMPLATE_CREATE_STATUS_INVALID,
                errors=tuple(errors),
            )

        template_id = self.print_settings_repo.create_print_settings(params)
        return CreatePrintSettingsResult(
            status=DOCUMENT_TEMPLATE_CREATE_STATUS_CREATED,
            template_id=template_id,
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
                include_legacy=False,
            )
        except ValueError as error:
            errors.append(str(error))

        return errors


CreatePrintSettingsUseCase = CreateDocumentTemplateUseCase
