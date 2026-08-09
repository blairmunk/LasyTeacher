"""Django implementation of the presentation profile repository."""

from typing import List, Optional

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    DocumentPresentationProfile,
    UpdatePresentationProfileParams,
)
from core_logic.interfaces.presentation_profile_repo import (
    IPresentationProfileRepository,
)
from document_engine.models import PresentationProfile


class DjangoPresentationProfileRepository(IPresentationProfileRepository):
    """Persist document presentation profiles with Django ORM."""

    def list_presentation_profiles(
        self,
        document_type: str = '',
    ) -> List[DocumentPresentationProfile]:
        queryset = PresentationProfile.objects.all()
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        return [
            profile.to_domain_profile()
            for profile in queryset
        ]

    def get_presentation_profile(
        self,
        presentation_profile_id: str,
        document_type: str = '',
    ) -> Optional[DocumentPresentationProfile]:
        queryset = PresentationProfile.objects.filter(
            pk=presentation_profile_id,
        )
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        profile = queryset.first()
        if profile is None:
            return None
        return profile.to_domain_profile()

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
