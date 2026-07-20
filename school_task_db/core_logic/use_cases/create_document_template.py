"""Create a sectioned document template."""

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    CreateDocumentTemplateResult,
)
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
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
        document_template_repo: IDocumentTemplateRepository,
    ):
        self.document_template_repo = document_template_repo

    def execute(
        self,
        params: CreateDocumentTemplateParams,
    ) -> CreateDocumentTemplateResult:
        errors = self._validate(params)
        if errors:
            return CreateDocumentTemplateResult(
                status=DOCUMENT_TEMPLATE_CREATE_STATUS_INVALID,
                errors=tuple(errors),
            )

        template_id = self.document_template_repo.create_template(params)
        return CreateDocumentTemplateResult(
            status=DOCUMENT_TEMPLATE_CREATE_STATUS_CREATED,
            template_id=template_id,
        )

    def _validate(self, params: CreateDocumentTemplateParams) -> list[str]:
        errors = []
        if not params.name:
            errors.append('Название шаблона обязательно.')
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
