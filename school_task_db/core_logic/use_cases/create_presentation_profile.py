"""Create a document presentation profile."""

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    CreatePresentationProfileResult,
)
from core_logic.interfaces.presentation_profile_command_repo import (
    IPresentationProfileCommandRepository,
)
from core_logic.value_objects.document_type_catalog import validate_document_type


PRESENTATION_PROFILE_CREATE_STATUS_CREATED = 'created'
PRESENTATION_PROFILE_CREATE_STATUS_INVALID = 'invalid'


class CreatePresentationProfileUseCase:
    """Validate and persist a document presentation profile."""

    def __init__(
        self,
        presentation_profile_repo: IPresentationProfileCommandRepository,
    ):
        self.presentation_profile_repo = presentation_profile_repo

    def execute(
        self,
        params: CreatePresentationProfileParams,
    ) -> CreatePresentationProfileResult:
        errors = self._validate(params)
        if errors:
            return CreatePresentationProfileResult(
                status=PRESENTATION_PROFILE_CREATE_STATUS_INVALID,
                errors=tuple(errors),
            )

        presentation_profile_id = (
            self.presentation_profile_repo.create_presentation_profile(
                params,
            )
        )
        return CreatePresentationProfileResult(
            status=PRESENTATION_PROFILE_CREATE_STATUS_CREATED,
            presentation_profile_id=presentation_profile_id,
        )

    def _validate(self, params: CreatePresentationProfileParams) -> list[str]:
        errors = []
        if not params.name:
            errors.append('Название профиля печати обязательно.')
        if not params.document_type:
            errors.append('Тип документа обязателен.')
        try:
            validate_document_type(params.document_type)
        except ValueError as error:
            errors.append(str(error))

        return errors
