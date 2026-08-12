"""Get one document presentation profile for editing."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.interfaces.presentation_profile_catalog_repo import (
    IPresentationProfileCatalogRepository,
)


@dataclass(frozen=True)
class GetPresentationProfileRequest:
    presentation_profile_id: str
    document_type: str = ''


@dataclass(frozen=True)
class GetPresentationProfileData:
    presentation_profile: DocumentPresentationProfile | None = None


class GetPresentationProfileUseCase:
    """Get one document presentation profile for editing."""

    def __init__(
        self,
        presentation_profile_repo: IPresentationProfileCatalogRepository,
    ):
        self.presentation_profile_repo = presentation_profile_repo

    def execute(
        self,
        request: GetPresentationProfileRequest,
    ) -> GetPresentationProfileData:
        return GetPresentationProfileData(
            presentation_profile=(
                self.presentation_profile_repo.get_presentation_profile(
                    presentation_profile_id=request.presentation_profile_id,
                    document_type=request.document_type,
                )
            ),
        )
