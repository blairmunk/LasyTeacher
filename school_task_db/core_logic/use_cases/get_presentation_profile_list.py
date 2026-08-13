"""Build document presentation profile list data."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.interfaces.presentation_profile_catalog_repo import (
    IPresentationProfileCatalogRepository,
)


@dataclass(frozen=True)
class GetPresentationProfileListRequest:
    document_type: str = ''


@dataclass(frozen=True)
class PresentationProfileListData:
    presentation_profiles: tuple[DocumentPresentationProfile, ...]


class GetPresentationProfileListUseCase:
    """Build document presentation profile list data."""

    def __init__(
        self,
        presentation_profile_repo: IPresentationProfileCatalogRepository,
    ):
        self.presentation_profile_repo = presentation_profile_repo

    def execute(
        self,
        request: GetPresentationProfileListRequest | None = None,
    ) -> PresentationProfileListData:
        request = request or GetPresentationProfileListRequest()
        return PresentationProfileListData(
            presentation_profiles=tuple(
                self.presentation_profile_repo.list_presentation_profiles(
                    document_type=request.document_type,
                )
            ),
        )
