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
from document_engine.models import PrintSettings


class DjangoPresentationProfileRepository(IPresentationProfileRepository):
    """Persist presentation profiles through the legacy Django model."""

    def list_presentation_profiles(
        self,
        document_type: str = '',
    ) -> List[DocumentPresentationProfile]:
        queryset = PrintSettings.objects.all()
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        return [
            print_settings.to_presentation_profile()
            for print_settings in queryset
        ]

    def get_presentation_profile(
        self,
        presentation_profile_id: str,
        document_type: str = '',
    ) -> Optional[DocumentPresentationProfile]:
        queryset = PrintSettings.objects.filter(pk=presentation_profile_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        print_settings = queryset.first()
        if print_settings is None:
            return None
        return print_settings.to_presentation_profile()

    def create_presentation_profile(
        self,
        params: CreatePresentationProfileParams,
    ) -> str:
        if params.is_default:
            PrintSettings.objects.filter(
                document_type=params.document_type,
                is_default=True,
            ).update(is_default=False)

        print_settings = PrintSettings(
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
        print_settings.full_clean()
        print_settings.save()
        return str(print_settings.pk)

    def update_presentation_profile(
        self,
        params: UpdatePresentationProfileParams,
    ) -> bool:
        print_settings = PrintSettings.objects.filter(
            pk=params.presentation_profile_id,
        ).first()
        if print_settings is None:
            return False

        if params.is_default:
            PrintSettings.objects.filter(
                document_type=params.document_type,
                is_default=True,
            ).exclude(pk=print_settings.pk).update(is_default=False)

        print_settings.name = params.name
        print_settings.description = params.description
        print_settings.document_type = params.document_type
        print_settings.is_default = params.is_default
        print_settings.custom_css = params.presentation.custom_css
        print_settings.custom_latex_preamble = (
            params.presentation.custom_latex_preamble
        )
        print_settings.html_template_override = (
            params.presentation.html_template_override
        )
        print_settings.latex_template_override = (
            params.presentation.latex_template_override
        )
        print_settings.full_clean()
        print_settings.save()
        return True
