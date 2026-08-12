"""Django command adapter for document presentation profiles."""

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    UpdatePresentationProfileParams,
)
from core_logic.interfaces.presentation_profile_command_repo import (
    IPresentationProfileCommandRepository,
)
from document_engine.models import PresentationProfile


class DjangoPresentationProfileCommandRepository(
    IPresentationProfileCommandRepository,
):
    def create_presentation_profile(
        self,
        params: CreatePresentationProfileParams,
    ) -> str:
        if params.is_default:
            PresentationProfile.objects.filter(
                document_type=params.document_type,
                is_default=True,
            ).update(is_default=False)

        profile = PresentationProfile(
            name=params.name,
            description=params.description,
            document_type=params.document_type,
            is_default=params.is_default,
            custom_css=params.presentation.custom_css,
            custom_latex_preamble=params.presentation.custom_latex_preamble,
            html_template_override=(
                params.presentation.html_template_override
            ),
            latex_template_override=(
                params.presentation.latex_template_override
            ),
        )
        profile.full_clean()
        profile.save()
        return str(profile.pk)

    def update_presentation_profile(
        self,
        params: UpdatePresentationProfileParams,
    ) -> bool:
        profile = PresentationProfile.objects.filter(
            pk=params.presentation_profile_id,
        ).first()
        if profile is None:
            return False

        if params.is_default:
            PresentationProfile.objects.filter(
                document_type=params.document_type,
                is_default=True,
            ).exclude(pk=profile.pk).update(is_default=False)

        profile.name = params.name
        profile.description = params.description
        profile.document_type = params.document_type
        profile.is_default = params.is_default
        profile.custom_css = params.presentation.custom_css
        profile.custom_latex_preamble = (
            params.presentation.custom_latex_preamble
        )
        profile.html_template_override = (
            params.presentation.html_template_override
        )
        profile.latex_template_override = (
            params.presentation.latex_template_override
        )
        profile.full_clean()
        profile.save()
        return True
