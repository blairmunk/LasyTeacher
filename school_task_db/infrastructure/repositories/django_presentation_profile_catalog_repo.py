"""Django read adapter for document presentation profiles."""

from typing import Optional

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.interfaces.presentation_profile_catalog_repo import (
    IPresentationProfileCatalogRepository,
)
from document_engine.models import PresentationProfile


class DjangoPresentationProfileCatalogRepository(
    IPresentationProfileCatalogRepository,
):
    def list_presentation_profiles(
        self,
        document_type: str = '',
    ) -> tuple[DocumentPresentationProfile, ...]:
        queryset = PresentationProfile.objects.all()
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        return tuple(profile.to_domain_profile() for profile in queryset)

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
