"""Update a document presentation profile."""

from core_logic.entities.document import (
    UpdatePresentationProfileParams,
    UpdatePresentationProfileResult,
)
from core_logic.interfaces.presentation_profile_command_repo import (
    IPresentationProfileCommandRepository,
)
from core_logic.value_objects.document_type_catalog import validate_document_type


PRESENTATION_PROFILE_UPDATE_STATUS_UPDATED = 'updated'
PRESENTATION_PROFILE_UPDATE_STATUS_INVALID = 'invalid'
PRESENTATION_PROFILE_UPDATE_STATUS_NOT_FOUND = 'not_found'


class UpdatePresentationProfileUseCase:
    """Validate and persist changes to a presentation profile."""

    def __init__(
        self,
        presentation_profile_repo: IPresentationProfileCommandRepository,
    ):
        self.presentation_profile_repo = presentation_profile_repo

    def execute(
        self,
        params: UpdatePresentationProfileParams,
    ) -> UpdatePresentationProfileResult:
        errors = self._validate(params)
        if errors:
            return UpdatePresentationProfileResult(
                status=PRESENTATION_PROFILE_UPDATE_STATUS_INVALID,
                presentation_profile_id=params.presentation_profile_id,
                errors=tuple(errors),
            )

        updated = self.presentation_profile_repo.update_presentation_profile(params)
        if not updated:
            return UpdatePresentationProfileResult(
                status=PRESENTATION_PROFILE_UPDATE_STATUS_NOT_FOUND,
                presentation_profile_id=params.presentation_profile_id,
            )
        return UpdatePresentationProfileResult(
            status=PRESENTATION_PROFILE_UPDATE_STATUS_UPDATED,
            presentation_profile_id=params.presentation_profile_id,
        )

    def _validate(self, params: UpdatePresentationProfileParams) -> list[str]:
        errors = []
        if not params.presentation_profile_id:
            errors.append('ID профиля печати обязателен.')
        if not params.name:
            errors.append('Название профиля печати обязательно.')
        if not params.document_type:
            errors.append('Тип документа обязателен.')
        try:
            validate_document_type(params.document_type)
        except ValueError as error:
            errors.append(str(error))

        return errors
